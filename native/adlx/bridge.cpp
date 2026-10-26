// Isolated, read-only ADLX worker. The upstream helper loader is NOT linked.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <wintrust.h>
#include <softpub.h>
#include <mscat.h>
#include <bcrypt.h>
#include <psapi.h>
#include <array>
#include <cassert>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include "ADLX.h"
#include "IPerformanceMonitoring.h"
static_assert(sizeof(void*)==8,"x64 only");
namespace lone {
constexpr unsigned count=7;
const std::array<const char*,count> ids={"utilization","temperature","hotspot_temperature","vram_used_mb","core_clock","power","fan_rpm"};
constexpr char expected_sha[]="992f6db497a3c8af8d26e578c7b7fce90ed67e506d7790cc3221e4a01b67852a";
struct Fault {const char* code;};
void need(bool ok,const char* code){if(!ok)throw Fault{code};}
struct Reading {std::string state="unavailable";double value=0;};
struct Cap {bool ok=false,supported=false;};
struct Device {std::string name="AMD Radeon RX 6750 XT",sdk="";int interval=0;Reading total;std::array<Cap,count> caps;};
struct TimeProbe {std::array<int64_t,3> deltas{};std::array<bool,3> usable{};unsigned matches=0;double age=-1;std::string selected="unverified",rule="clock_unmatched";};
struct Frame {int64_t stamp=0;double age=-1;std::string clock="unverified";std::array<Reading,count> readings;bool warming=false;TimeProbe probe;};
std::string quote(const std::string& text){
    need(text.size()<=256,"text_limit");std::ostringstream s;s<<'"';
    for(unsigned char ch:text){if(ch=='"'||ch=='\\')s<<'\\'<<ch;else if(ch>=32&&ch<127)s<<ch;else s<<'?';}s<<'"';return s.str();
}
std::string reading(const Reading& r){
    std::ostringstream s;s<<"{\"state\":"<<quote(r.state)<<",\"value\":";
    if(r.state!="available")s<<"null";else{need(std::isfinite(r.value),"invalid_value");s<<std::setprecision(15)<<r.value;}s<<'}';return s.str();
}
void emit(const std::string& value){need(value.size()<=16384,"message_limit");std::cout<<value<<'\n'<<std::flush;}
void phase(const char* code){emit("{\"v\":1,\"event\":\"phase\",\"code\":"+quote(code)+"}");}
void error(const char* code){emit("{\"v\":1,\"event\":\"error\",\"code\":"+quote(code)+"}");}
double age_at(int64_t stamp,uint64_t uptime,uint64_t unix_ms,uint64_t windows_ms,std::string& source,TimeProbe* diagnostic=nullptr){
    if(diagnostic)*diagnostic=TimeProbe{};
    if(stamp<0){if(diagnostic)diagnostic->rule="timestamp_negative";return -1;}const std::array<uint64_t,3> now={uptime,unix_ms,windows_ms};
    const std::array<const char*,3> names={"uptime_ms","unix_ms","windows_ms"};double age=-1;unsigned matches=0;
    for(unsigned i=0;i<now.size();++i){
        if(diagnostic&&now[i]<=INT64_MAX){diagnostic->deltas[i]=static_cast<int64_t>(now[i])-stamp;diagnostic->usable[i]=true;}
        if(static_cast<uint64_t>(stamp)<=now[i]&&now[i]-static_cast<uint64_t>(stamp)<=5000){
            age=static_cast<double>(now[i]-static_cast<uint64_t>(stamp))/1000;source=names[i];++matches;}}
    if(diagnostic){diagnostic->matches=matches;diagnostic->age=matches==1?age:-1;diagnostic->selected=source;
        diagnostic->rule=matches==1?"clock_matched":matches>1?"clock_ambiguous":"clock_unmatched";}
    return matches==1?age:-1;
}
bool runtime_facts(bool fixed_path,bool x64,bool signature,const std::string& sha,bool elevated){return fixed_path&&x64&&signature&&sha==expected_sha&&!elevated;}
bool memory_ok(uint64_t bytes){return bytes<=512ULL*1024*1024;}
bool history_warming(ADLX_RESULT result,uint64_t since_start){return since_start<=5000&&(result==ADLX_NOT_FOUND||result==ADLX_PENDING_OPERATION);}
struct Backend {virtual ~Backend()=default;virtual Device open()=0;virtual Frame latest()=0;virtual bool close()=0;};
#ifndef LONE_ADLX_MOCK
template<class T>struct Ref{
    T* p=nullptr;~Ref(){reset();}Ref()=default;Ref(const Ref&)=delete;Ref& operator=(const Ref&)=delete;
    void reset(){if(p){p->Release();p=nullptr;}}T** put(){reset();return &p;}T* operator->()const{return p;}explicit operator bool()const{return p!=nullptr;}
};
struct Handle{HANDLE p=INVALID_HANDLE_VALUE;~Handle(){if(p!=INVALID_HANDLE_VALUE)CloseHandle(p);}};
bool elevated(){
    HANDLE raw=nullptr;need(OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&raw)!=0,"token_query_failed");Handle token;token.p=raw;
    TOKEN_ELEVATION info{};DWORD size=0;need(GetTokenInformation(token.p,TokenElevation,&info,sizeof(info),&size)!=0,"token_query_failed");return info.TokenIsElevated!=0;
}
std::string hash_file(HANDLE file){
    BCRYPT_ALG_HANDLE alg=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    need(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"hash_failed");
    if(BCryptCreateHash(alg,&hash,nullptr,0,nullptr,0,0)<0){BCryptCloseAlgorithmProvider(alg,0);throw Fault{"hash_failed"};}
    LARGE_INTEGER zero{};bool ok=SetFilePointerEx(file,zero,nullptr,FILE_BEGIN)!=0;std::array<UCHAR,65536> buffer{};DWORD got=0;
    while(ok){if(!ReadFile(file,buffer.data(),static_cast<DWORD>(buffer.size()),&got,nullptr)){ok=false;break;}if(!got)break;if(BCryptHashData(hash,buffer.data(),got,0)<0){ok=false;break;}}
    std::array<UCHAR,32> digest{};if(ok)ok=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0)>=0;
    BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(alg,0);need(ok,"hash_failed");std::ostringstream s;s<<std::hex<<std::setfill('0');for(auto b:digest)s<<std::setw(2)<<static_cast<unsigned>(b);return s.str();
}
LONG verify_trust(WINTRUST_DATA& trust){
    trust.cbStruct=sizeof(trust);trust.dwUIChoice=WTD_UI_NONE;trust.fdwRevocationChecks=WTD_REVOKE_WHOLECHAIN;
    trust.dwStateAction=WTD_STATEACTION_VERIFY;trust.dwProvFlags=WTD_CACHE_ONLY_URL_RETRIEVAL|WTD_REVOCATION_CHECK_CHAIN_EXCLUDE_ROOT;
    GUID policy=WINTRUST_ACTION_GENERIC_VERIFY_V2;LONG status=WinVerifyTrust(nullptr,&policy,&trust);
    trust.dwStateAction=WTD_STATEACTION_CLOSE;WinVerifyTrust(nullptr,&policy,&trust);return status;
}
bool catalog_signature(HANDLE file,const std::wstring& path){
    auto library=GetModuleHandleW(L"wintrust.dll");
    auto acquire=reinterpret_cast<decltype(&CryptCATAdminAcquireContext2)>(GetProcAddress(library,"CryptCATAdminAcquireContext2"));
    auto calculate=reinterpret_cast<decltype(&CryptCATAdminCalcHashFromFileHandle2)>(GetProcAddress(library,"CryptCATAdminCalcHashFromFileHandle2"));
    if(!acquire||!calculate)return false;
    HCATADMIN admin=nullptr;GUID subsystem=DRIVER_ACTION_VERIFY;
    if(!acquire(&admin,&subsystem,BCRYPT_SHA256_ALGORITHM,nullptr,0))return false;
    std::array<BYTE,64> hash{};DWORD length=static_cast<DWORD>(hash.size());bool valid=false;HCATINFO catalog=nullptr;
    if(calculate(admin,file,&length,hash.data(),0)&&length>0&&length<=hash.size()){
        std::wostringstream tag;tag<<std::uppercase<<std::hex<<std::setfill(L'0');for(DWORD i=0;i<length;++i)tag<<std::setw(2)<<static_cast<unsigned>(hash[i]);
        const auto member=tag.str();
        for(unsigned n=0;n<8;++n){
            catalog=CryptCATAdminEnumCatalogFromHash(admin,hash.data(),length,0,&catalog);if(!catalog)break;
            CATALOG_INFO info{};info.cbStruct=sizeof(info);if(!CryptCATCatalogInfoFromContext(catalog,&info,0))break;
            WINTRUST_CATALOG_INFO ci{};ci.cbStruct=sizeof(ci);ci.pcwszCatalogFilePath=info.wszCatalogFile;
            ci.pcwszMemberTag=member.c_str();ci.pcwszMemberFilePath=path.c_str();ci.hMemberFile=file;
            ci.pbCalculatedFileHash=hash.data();ci.cbCalculatedFileHash=length;ci.hCatAdmin=admin;
            WINTRUST_DATA trust{};trust.dwUnionChoice=WTD_CHOICE_CATALOG;trust.pCatalog=&ci;
            if(verify_trust(trust)==ERROR_SUCCESS){valid=true;break;}
        }
    }
    if(catalog)CryptCATAdminReleaseCatalogContext(admin,catalog,0);CryptCATAdminReleaseContext(admin,0);return valid;
}
class Adlx final:public Backend{
    Handle file_;HMODULE module_=nullptr;ADLXTerminate_Fn terminate_=nullptr;adlx::IADLXSystem* system_=nullptr;
    bool initialized_=false,tracking_=false,closed_=false;uint64_t tracking_started_=0;Ref<adlx::IADLXGPU> gpu_;Ref<adlx::IADLXPerformanceMonitoringServices> perf_;
    Ref<adlx::IADLXGPUMetricsSupport> support_;Device device_;
public:
    ~Adlx()override{close();}
    std::wstring verify_runtime(){
        need(!elevated(),"elevation_refused");wchar_t folder[32768]{};UINT n=GetSystemDirectoryW(folder,32768);need(n>0&&n<32700,"system_path_failed");
        std::wstring path=std::wstring(folder)+L"\\amdadlx64.dll";
        file_.p=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);need(file_.p!=INVALID_HANDLE_VALUE,"runtime_open_failed");
        wchar_t final_path[32768]{};DWORD f=GetFinalPathNameByHandleW(file_.p,final_path,32768,FILE_NAME_NORMALIZED|VOLUME_NAME_DOS);
        need(f>0&&f<32768&&_wcsicmp(final_path,(L"\\\\?\\"+path).c_str())==0,"runtime_path_mismatch");
        IMAGE_DOS_HEADER dos{};DWORD got=0;need(ReadFile(file_.p,&dos,sizeof(dos),&got,nullptr)&&got==sizeof(dos)&&dos.e_magic==IMAGE_DOS_SIGNATURE,"invalid_pe");
        need(dos.e_lfanew>=0&&dos.e_lfanew<1048576,"invalid_pe");LARGE_INTEGER pos{};pos.QuadPart=dos.e_lfanew;need(SetFilePointerEx(file_.p,pos,nullptr,FILE_BEGIN)!=0,"invalid_pe");
        DWORD signature=0;IMAGE_FILE_HEADER pe{};
        need(ReadFile(file_.p,&signature,sizeof(signature),&got,nullptr)&&got==sizeof(signature)&&signature==IMAGE_NT_SIGNATURE,"invalid_pe");
        need(ReadFile(file_.p,&pe,sizeof(pe),&got,nullptr)&&got==sizeof(pe)&&pe.Machine==IMAGE_FILE_MACHINE_AMD64,"runtime_not_x64");
        std::string sha=hash_file(file_.p);need(sha==expected_sha,"runtime_hash_mismatch");
        WINTRUST_FILE_INFO fi{};fi.cbStruct=sizeof(fi);fi.pcwszFilePath=path.c_str();fi.hFile=file_.p;
        WINTRUST_DATA trust{};trust.dwUnionChoice=WTD_CHOICE_FILE;trust.pFile=&fi;
        LONG status=verify_trust(trust);
        bool signed_ok=status==ERROR_SUCCESS;
        // A catalog is checked only for a file without an embedded signature.
        if(!signed_ok&&status==TRUST_E_NOSIGNATURE)signed_ok=catalog_signature(file_.p,path);
        need(runtime_facts(true,true,signed_ok,sha,false),"runtime_signature_rejected");phase("runtime_verified");return path;
    }
    Device open()override{
        auto path=verify_runtime();
        module_=LoadLibraryExW(path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(module_!=nullptr,"runtime_load_failed");
        wchar_t loaded[32768]{};DWORD length=GetModuleFileNameW(module_,loaded,32768);need(length>0&&length<32768&&_wcsicmp(loaded,path.c_str())==0,"loaded_path_mismatch");phase("adlx_loaded");
        auto initialize=reinterpret_cast<ADLXInitialize_Fn>(GetProcAddress(module_,ADLX_INIT_FUNCTION_NAME));
        terminate_=reinterpret_cast<ADLXTerminate_Fn>(GetProcAddress(module_,ADLX_TERMINATE_FUNCTION_NAME));
        auto version=reinterpret_cast<ADLXQueryVersion_Fn>(GetProcAddress(module_,ADLX_QUERY_VERSION_FUNCTION_NAME));need(initialize&&terminate_&&version,"runtime_exports_missing");
        auto init_result=initialize(ADLX_FULL_VERSION,&system_);need(ADLX_SUCCEEDED(init_result)&&system_,"adlx_initialize_failed");initialized_=true;phase("adlx_initialized");
        const char* sdk=nullptr;if(version(&sdk)==ADLX_OK&&sdk&&strnlen_s(sdk,128)<128)device_.sdk=sdk;
        Ref<adlx::IADLXGPUList> list;need(system_->GetGPUs(list.put())==ADLX_OK&&list,"gpu_enumeration_failed");need(list->Size()>0&&list->Size()<=16,"gpu_count_invalid");unsigned selected=0;
        for(adlx_uint i=list->Begin();i<list->End();++i){
            Ref<adlx::IADLXGPU> candidate;need(list->At(i,candidate.put())==ADLX_OK&&candidate,"gpu_enumeration_failed");
            const char* vendor=nullptr;const char* name=nullptr;ADLX_GPU_TYPE type=GPUTYPE_UNDEFINED;
            if(candidate->VendorId(&vendor)!=ADLX_OK||!vendor||strnlen_s(vendor,16)>=16||candidate->Name(&name)!=ADLX_OK||!name||strnlen_s(name,128)>=128||candidate->Type(&type)!=ADLX_OK)continue;
            std::string normalized;for(unsigned char ch:std::string(name))if(ch>='a'&&ch<='z')normalized+=static_cast<char>(ch-'a'+'A');else if((ch>='A'&&ch<='Z')||(ch>='0'&&ch<='9'))normalized+=static_cast<char>(ch);
            bool amd=std::string(vendor)=="1002"||std::string(vendor)=="0x1002"||std::string(vendor)=="0X1002";
            if(amd&&type==GPUTYPE_DISCRETE&&(normalized=="AMDRADEONRX6750XT"||normalized=="RADEONRX6750XT")){++selected;gpu_.reset();gpu_.p=candidate.p;candidate.p=nullptr;device_.name=name;}
        }
        need(selected==1,"gpu_selection_failed");need(system_->GetPerformanceMonitoringServices(perf_.put())==ADLX_OK&&perf_,"performance_service_failed");
        need(perf_->GetSupportedGPUMetrics(gpu_.p,support_.put())==ADLX_OK&&support_,"capability_discovery_failed");
        using Query=ADLX_RESULT(ADLX_STD_CALL adlx::IADLXGPUMetricsSupport::*)(adlx_bool*);
        const std::array<Query,count> queries={&adlx::IADLXGPUMetricsSupport::IsSupportedGPUUsage,&adlx::IADLXGPUMetricsSupport::IsSupportedGPUTemperature,
            &adlx::IADLXGPUMetricsSupport::IsSupportedGPUHotspotTemperature,&adlx::IADLXGPUMetricsSupport::IsSupportedGPUVRAM,
            &adlx::IADLXGPUMetricsSupport::IsSupportedGPUClockSpeed,&adlx::IADLXGPUMetricsSupport::IsSupportedGPUPower,&adlx::IADLXGPUMetricsSupport::IsSupportedGPUFanSpeed};
        for(unsigned i=0;i<count;++i){adlx_bool yes=false;device_.caps[i].ok=(support_.p->*queries[i])(&yes)==ADLX_OK;device_.caps[i].supported=device_.caps[i].ok&&yes;}
        adlx_uint total=0;if(gpu_->TotalVRAM(&total)==ADLX_OK&&total>0)device_.total={"available",static_cast<double>(total)};
        adlx_int interval=0;if(perf_->GetSamplingInterval(&interval)==ADLX_OK)device_.interval=interval;
        auto tracking_result=perf_->StartPerformanceMetricsTracking();need(ADLX_SUCCEEDED(tracking_result),"tracking_start_failed");tracking_=true;tracking_started_=GetTickCount64();return device_;
    }
    Frame latest()override{
        Frame frame;Ref<adlx::IADLXGPUMetricsList> list;auto result=perf_->GetGPUMetricsHistory(gpu_.p,0,0,list.put());
        if(history_warming(result,GetTickCount64()-tracking_started_)){frame.warming=true;return frame;}
        need(result==ADLX_OK&&list,"metrics_query_failed");
        need(list->Size()<=8,"history_limit");if(!list->Size()){frame.warming=true;return frame;}
        Ref<adlx::IADLXGPUMetrics> metrics;need(list->At(list->End()-1,metrics.put())==ADLX_OK&&metrics,"metrics_query_failed");
        adlx_int64 stamp=0;need(metrics->TimeStamp(&stamp)==ADLX_OK&&stamp>=0,"timestamp_failed");frame.stamp=stamp;
        FILETIME ft{};GetSystemTimePreciseAsFileTime(&ft);ULARGE_INTEGER ticks{};ticks.LowPart=ft.dwLowDateTime;ticks.HighPart=ft.dwHighDateTime;
        uint64_t ms=ticks.QuadPart/10000;frame.age=age_at(stamp,GetTickCount64(),ms-11644473600000ULL,ms,frame.clock,&frame.probe);
        for(unsigned i=0;i<count;++i){
            const auto& cap=device_.caps[i];if(!cap.ok)continue;if(!cap.supported){frame.readings[i].state="unsupported";continue;}
            ADLX_RESULT r=ADLX_FAIL;adlx_double decimal=0;adlx_int integer=0;bool whole=false;
            switch(i){case 0:r=metrics->GPUUsage(&decimal);break;case 1:r=metrics->GPUTemperature(&decimal);break;case 2:r=metrics->GPUHotspotTemperature(&decimal);break;
            case 3:r=metrics->GPUVRAM(&integer);whole=true;break;case 4:r=metrics->GPUClockSpeed(&integer);whole=true;break;case 5:r=metrics->GPUPower(&decimal);break;case 6:r=metrics->GPUFanSpeed(&integer);whole=true;break;}
            frame.readings[i]=r==ADLX_OK?Reading{"available",whole?static_cast<double>(integer):decimal}:Reading{"error",0};
        }
        return frame;
    }
    bool close()override{
        if(closed_)return true;closed_=true;bool clean=true;if(tracking_){clean=perf_->StopPerformanceMetricsTracking()==ADLX_OK;tracking_=false;}
        support_.reset();gpu_.reset();perf_.reset();system_=nullptr;if(initialized_){clean=terminate_()==ADLX_OK&&clean;initialized_=false;}
        if(module_){clean=FreeLibrary(module_)!=0&&clean;module_=nullptr;}return clean;
    }
};
#else
class Fake final:public Backend{
    std::string scenario_;int64_t stamp_=10000;unsigned reads_=0;bool diagnostics_=false;
public:
    explicit Fake(std::string scenario,bool diagnostics=false):scenario_(std::move(scenario)),diagnostics_(diagnostics){}
    Device open()override{
        if(scenario_=="load_fail")throw Fault{"runtime_load_failed"};if(scenario_=="init_fail")throw Fault{"adlx_initialize_failed"};
        Device d;d.sdk="fixture";d.interval=1000;d.total={"available",12288};for(auto& cap:d.caps)cap={true,true};
        if(scenario_=="unsupported")d.caps[2]={true,false};if(scenario_=="cap_error")d.caps[6]={false,false};return d;
    }
    Frame latest()override{
        ++reads_;if(scenario_=="read_fail"&&reads_==1)throw Fault{"metrics_query_failed"};if(scenario_=="slow")Sleep(700);
        Frame f;f.stamp=stamp_+=2000;f.age=scenario_=="stale"?10:0.1;f.clock="fixture";
        if(diagnostics_||scenario_=="unverified"){
            uint64_t uptime=static_cast<uint64_t>(f.stamp)+(scenario_=="unverified"?100000:100);
            f.clock="unverified";f.age=age_at(f.stamp,uptime,1790000000000ULL,13434473600000ULL,f.clock,&f.probe);
        }
        const std::array<double,count> values={12.5,42,52,1024,500,18,0};for(unsigned i=0;i<count;++i)f.readings[i]={"available",values[i]};
        if(scenario_=="unsupported")f.readings[2].state="unsupported";if(scenario_=="cap_error")f.readings[6].state="unavailable";
        if(scenario_=="invalid")f.readings[0].value=101;if(scenario_=="warming"&&reads_==1)f.warming=true;return f;
    }
    bool close()override{return scenario_!="close_fail";}
};
void self_test(){
    assert(runtime_facts(true,true,true,expected_sha,false));assert(!runtime_facts(false,true,true,expected_sha,false));assert(!runtime_facts(true,false,true,expected_sha,false));
    assert(!runtime_facts(true,true,false,expected_sha,false));assert(!runtime_facts(true,true,true,"bad",false));assert(!runtime_facts(true,true,true,expected_sha,true));
    std::string source;assert(std::abs(age_at(9900,10000,10000000,10000000000,source)-.1)<1e-9&&source=="uptime_ms");
    assert(age_at(-1,10000,10000000,10000000000,source)<0);assert(age_at(10100,10000,10000000,10000000000,source)<0);
    assert(age_at(1,10000,10000000,10000000000,source)<0);assert(age_at(10000,10000,10000,10000000000,source)<0);
    assert(reading({"unsupported",0}).find("null")!=std::string::npos);assert(reading({"available",0}).find(":0")!=std::string::npos);
    assert(memory_ok(512ULL*1024*1024));assert(!memory_ok(512ULL*1024*1024+1));
    assert(history_warming(ADLX_PENDING_OPERATION,0));assert(history_warming(ADLX_NOT_FOUND,5000));
    assert(!history_warming(ADLX_NOT_FOUND,5001));assert(!history_warming(ADLX_FAIL,0));
    TimeProbe probe;source="unverified";age_at(9900,10000,10000000,10000000000,source,&probe);
    assert(probe.matches==1);assert(probe.deltas[0]==100);assert(probe.rule=="clock_matched");
    source="unverified";assert(age_at(9000,10000,10000000,10000000000,source,&probe)==1);
    source="unverified";age_at(0,100000,10000000,10000000000,source,&probe);assert(probe.matches==0);assert(probe.rule=="clock_unmatched");
    source="unverified";age_at(10001,10000,10000000,10000000000,source,&probe);assert(probe.deltas[0]==-1);
    source="unverified";age_at(1000,1000,1000,1000,source,&probe);assert(probe.matches==3);assert(probe.rule=="clock_ambiguous");
    source="unverified";age_at(-1,1000,1000,1000,source,&probe);assert(probe.rule=="timestamp_negative");
    source="unverified";age_at(1790000000,100000,1790000000000ULL,13434473600000ULL,source,&probe);assert(probe.matches==0);
    source="unverified";assert(age_at(0,0,10000000,10000000000,source,&probe)==0);
    emit("{\"ok\":true,\"checks\":31,\"simulated\":true}");
}
#endif
std::string ready(const Device& d,bool simulated,bool diagnostics=false){
    std::ostringstream s;s<<"{\"v\":1,\"event\":\"ready\",\"simulated\":"<<(simulated?"true":"false")<<",\"pid\":"<<GetCurrentProcessId()
      <<",\"device\":{\"key\":\"amd-rx6750xt\",\"name\":"<<quote(d.name)<<",\"vendor_id\":4098,\"discrete\":true},\"sdk_version\":"<<quote(d.sdk)
      <<",\"sdk_interval_ms\":"<<d.interval<<",\"total_vram_mb\":"<<reading(d.total)<<",\"capabilities\":{";
    for(unsigned i=0;i<count;++i){if(i)s<<',';s<<quote(std::string("gpu.adlx.")+ids[i])<<":{\"ok\":"<<(d.caps[i].ok?"true":"false")<<",\"supported\":"<<(d.caps[i].supported?"true":"false")<<'}';}
    s<<'}';if(diagnostics)s<<",\"diagnostic_profile\":\"adlx_frame_diagnostics_v1\"";s<<'}';return s.str();
}
std::string frame_json(const Frame& f,bool diagnostics=false){
    if(f.warming)return "{\"v\":1,\"event\":\"warming_up\"}";
    std::ostringstream s;s<<std::setprecision(15)<<"{\"v\":1,\"event\":\"frame\",\"timestamp_ms\":"<<f.stamp<<",\"age_seconds\":";
    if(f.age<0)s<<"null";else s<<f.age;s<<",\"clock_source\":"<<quote(f.clock)<<",\"readings\":{";
    for(unsigned i=0;i<count;++i){if(i)s<<',';s<<quote(std::string("gpu.adlx.")+ids[i])<<':'<<reading(f.readings[i]);}s<<'}';
    if(diagnostics){
        const auto& p=f.probe;s<<",\"diagnostic\":{\"profile\":\"adlx_frame_diagnostics_v1\",\"rule\":"<<quote(p.rule)
          <<",\"timestamp_unit\":\"milliseconds\",\"age_unit\":\"seconds\",\"match_count\":"<<p.matches<<",\"converted_age_seconds\":";
        if(p.age<0)s<<"null";else s<<p.age;s<<",\"selected_clock\":"<<quote(p.selected)<<",\"deltas_ms\":{";
        const std::array<const char*,3> names={"uptime_ms","unix_ms","windows_ms"};
        for(unsigned i=0;i<3;++i){if(i)s<<',';s<<quote(names[i])<<':';if(p.usable[i])s<<p.deltas[i];else s<<"null";}s<<"}}";
    }
    s<<'}';return s.str();
}
int run(Backend& backend,bool simulated,bool diagnostics=false){
    uint64_t start=GetTickCount64(),last=0;unsigned requests=0;int result=0;
    try{
        need(GetFileType(GetStdHandle(STD_INPUT_HANDLE))==FILE_TYPE_PIPE&&GetFileType(GetStdHandle(STD_OUTPUT_HANDLE))==FILE_TYPE_PIPE,"private_transport_required");
        emit(ready(backend.open(),simulated,diagnostics));std::string command;HANDLE input=GetStdHandle(STD_INPUT_HANDLE);bool done=false;
        while(!done&&GetTickCount64()-start<82000){
            DWORD available=0;if(!PeekNamedPipe(input,nullptr,0,nullptr,&available,nullptr))break;if(!available){Sleep(25);continue;}
            char ch=0;DWORD got=0;if(!ReadFile(input,&ch,1,&got,nullptr)||!got)break;if(ch=='\r')continue;
            if(ch!='\n'){need(command.size()<32,"command_limit");command+=ch;continue;}
            if(command=="stop"){done=true;continue;}need(command=="latest","invalid_command");command.clear();
            auto now=GetTickCount64();if(last&&now-last<1000){error("rate_limited");continue;}need(++requests<=45,"request_limit");last=now;
            PROCESS_MEMORY_COUNTERS memory{};memory.cb=sizeof(memory);need(GetProcessMemoryInfo(GetCurrentProcess(),&memory,sizeof(memory))!=0,"resource_query_failed");
            need(memory_ok(memory.WorkingSetSize),"memory_budget_exceeded");
            try{emit(frame_json(backend.latest(),diagnostics));}catch(const Fault& f){error(f.code);}
        }
    }catch(const Fault& f){error(f.code);result=1;}catch(...){error("bridge_internal_error");result=1;}
    bool clean=backend.close();emit(std::string("{\"v\":1,\"event\":\"stopped\",\"clean\":")+(clean?"true":"false")+"}");return clean?result:2;
}
}
int main(int argc,char** argv){
    using namespace lone;
#ifdef LONE_ADLX_MOCK
    if(argc==2&&std::string(argv[1])=="--self-test"){self_test();return 0;}
    bool diagnostics=argc==3&&std::string(argv[2])=="--diagnostics";
    if(argc>3||(argc==3&&!diagnostics)){error("arguments_refused");return 1;}
    Fake backend(argc>=2?argv[1]:"normal",diagnostics);return run(backend,true,diagnostics);
#else
    bool diagnostics=argc==2&&std::string(argv[1])=="--diagnostics";
    if(argc!=1&&!diagnostics){error("arguments_refused");return 1;}Adlx backend;
#ifdef LONE_ADLX_VERIFY
    try{backend.verify_runtime();return 0;}catch(const Fault& f){error(f.code);return 1;}
#else
    return run(backend,false,diagnostics);
#endif
#endif
}

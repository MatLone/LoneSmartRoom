"""Bounded PT-BR view model and escaped static review; no renderer bridge or I/O."""
from html import escape
import json

from .contracts import Component, DetailCode as D, DiagnosticError, tick
from .evidence import boolean, exact, utc_string

TITLES={Component.HTTPS:'Agente HTTPS',Component.LISTENER:'Listener esperado · 8776',
        Component.IPC:'Named Pipe de monitoramento',Component.CPU:'Coletor CPU',
        Component.GPU:'Coletor GPU',Component.RAM:'Coletor RAM',
        Component.ADLX:'Ponte AMD ADLX',Component.STARTUP:'Inicialização após login'}
LABELS={'healthy':'Saudável','offline':'Indisponível','unknown':'Indisponível',
        'unavailable':'Indisponível','unsupported':'Indisponível','stale':'Desatualizado','error':'Falha'}
DETAILS={
 D.NORMAL_INACTIVE:'Aplicativo Windows fechado e componentes ausentes. Inatividade normal; não é falha comprovada.',
 D.PASSIVE_UNVERIFIED:'Sem recibo atual acessível por uma interface de leitura autorizada. Nenhum componente foi iniciado.',
 D.HTTPS_OK:'Resposta autenticada, identidade TLS e pin confirmados pelo recibo.',
 D.CONNECTION_FAILED:'Sem resposta atual do agente. Isso não confirma PC desligado.',
 D.TLS_FAILED:'A identidade TLS não foi confirmada. A conexão não deve ser aceita.',
 D.AUTH_FAILED:'A autenticação não foi confirmada; nenhuma permissão foi concedida.',
 D.HTTP_FAILED:'O endpoint de status não apresentou uma resposta válida.',
 D.LISTENER_MISMATCH:'A porta existe, mas a identidade completa do processo não foi confirmada.',
 D.LISTENER_OK:'Imagem, criação e parentesco do listener esperado confirmados no recibo. Isso não prova autenticação HTTPS.',
 D.PIPE_DISCONNECTED:'Sem comunicação atual com o transporte local.',
 D.PIPE_IDENTITY_FAILED:'SID, sessão, localidade ou identidade do servidor não confirmados.',
 D.PIPE_CONTRACT_FAILED:'Versão do contrato local incompatível.',
 D.PIPE_LIMIT:'Mensagem recusada por formato ou limite do transporte.',
 D.METRICS_OK:'As leituras exigidas estão válidas dentro da cadência informada.',
 D.METRICS_PARTIAL:'Leituras suportadas válidas; existem sensores explicitamente não suportados.',
 D.METRICS_MISSING:'Coletor ausente ou leituras necessárias ainda indisponíveis.',
 D.METRICS_READ_ERROR:'Erro, acesso negado ou inconsistência nas leituras; valores não foram corrigidos artificialmente.',
 D.METRICS_WARMING:'Contadores em aquecimento. Aguardar uma amostra representativa.',
 D.METRICS_UNSUPPORTED:'Não há sensores dinâmicos suportados suficientes para confirmar saúde.',
 D.METRICS_STALE:'Há amostras antigas. Consultar novamente o cache não as torna atuais.',
 D.AWAITING_FRESH:'Retomada em atualização; aguardando amostra GPU nova e válida.',
 D.ADLX_NOT_RUNNING:'A ponte não está ativa ou sua execução não foi confirmada.',
 D.ADLX_UNVERIFIED:'A biblioteca não foi verificada. Nenhum carregamento é feito pelo diagnóstico.',
 D.ADLX_REJECTED:'Nenhum quadro atual válido: rejeição, aquecimento ou indisponibilidade. Sem reinício automático.',
 D.ADLX_OK:'Ponte e último quadro validados no recibo; não prova disponibilidade de todo sensor.',
 D.STARTUP_NOT_CONFIGURED:'Entrada de inicialização ausente no recibo; nenhuma entrada será criada.',
 D.STARTUP_TARGET_INVALID:'Destino da inicialização não confirmado. Não alterar caminhos automaticamente.',
 D.STARTUP_NOT_VERIFIED:'Faltam evidências correlacionadas de login, sessão, processo ou bootstrap.',
 D.STARTUP_DISPATCH_UNCONFIRMED:'Não foi possível distinguir execução manual de despacho após login.',
 D.STARTUP_BOOTSTRAP_FAILED:'Falha de bootstrap observada em tentativa correlacionada; não reiniciar.',
 D.STARTUP_BOOTSTRAP_SEEN:'Bootstrap correlacionado observado. O estado HTTPS é uma verificação separada.',
 D.STARTUP_EXITED:'Há registro de retorno do agente. Não confirma falha do mecanismo de login.',
 D.STARTUP_EXISTING_INSTANCE:'Outra instância foi detectada. Não reiniciar nem concluir falha do mecanismo de login.',
}
ERROR_CODES={'provider_failure','provider_timeout'}
PRIMARY_UNKNOWN={'not_observed','insufficient_evidence','invalid_time','out_of_order','conflicting_startup_evidence'}
PRIMARY_CODES=PRIMARY_UNKNOWN|ERROR_CODES|{
 'provider_unknown','provider_unavailable','provider_error','provider_unsupported','observation_stale',
 'authenticated_https','no_authenticated_response','unverified_identity','listener_absent',
 'expected_listener','listener_identity_mismatch','ipc_disconnected','ipc_contract_mismatch',
 'ipc_peer_unverified','validated_ipc','component_not_running','native_library_unverified',
 'sample_stale','sample_invalid','valid_sample','startup_not_configured','bootstrap_failure_observed',
 'bootstrap_observed','possible_dispatch_problem_unconfirmed'}
FALLBACK_TEXT={'expected_listener':'Listener esperado confirmado no recibo; HTTPS é uma verificação separada.',
 'listener_absent':'Listener não encontrado no recibo. Isso não confirma PC desligado.',
 'validated_ipc':'Peer local e contrato confirmados; leituras são verificadas separadamente.',
 'valid_sample':'Leitura válida na evidência recebida.',
 'authenticated_https':'Status autenticado confirmado no recibo.',
 'bootstrap_observed':'Bootstrap observado; não confirma disponibilidade atual do HTTPS.'}


def present(report, *, allow_observed=False):
    exact(report,('schema_version','generated_at','mode','simulation','repair_capability','power_state','checks'))
    if (type(report['schema_version']) is not int or report['schema_version']!=1
            or type(report['simulation']) is not bool
            or (not report['simulation'] and not allow_observed) or report['repair_capability'] is not False
            or report['power_state']!='unknown' or report['mode'] not in ('active','inactive')):
        raise DiagnosticError('invalid_diagnostic_report')
    utc_string(report['generated_at'])
    if type(report['checks']) is not list or len(report['checks'])!=len(Component):
        raise DiagnosticError('invalid_diagnostic_check_count')
    cards=[];seen=set()
    for r in report['checks']:
        exact(r,('component','state','code','evidence_kind','observed_at','age_seconds','valid','freshness_seconds','last_communication'),('detail_code',))
        try:component=Component(r['component'])
        except (ValueError,TypeError):raise DiagnosticError('invalid_presented_component') from None
        kind = 'simulated' if report['simulation'] else 'observed'
        if component in seen or type(r['state']) is not str or r['state'] not in LABELS or r['evidence_kind']!=kind:
            raise DiagnosticError('invalid_presented_state')
        seen.add(component);boolean(r['valid'])
        if r['valid']!=(r['state']=='healthy'):raise DiagnosticError('invalid_presented_validity')
        if r['observed_at'] is not None:utc_string(r['observed_at'])
        if r['last_communication'] is not None:
            utc_string(r['last_communication'])
            if component!=Component.HTTPS:raise DiagnosticError('unexpected_communication_timestamp')
        if r['age_seconds'] is not None:tick(r['age_seconds'])
        if tick(r['freshness_seconds']) not in (3,5,10,11,15,300):raise DiagnosticError('unexpected_diagnostic_freshness')
        if type(r['code']) is not str or r['code'] not in PRIMARY_CODES:raise DiagnosticError('invalid_diagnostic_code')
        if r['valid'] and (r['observed_at'] is None or r['age_seconds'] is None
                or r['age_seconds']>=r['freshness_seconds'] or utc_string(r['observed_at'])>utc_string(report['generated_at'])):
            raise DiagnosticError('presented_health_not_current')
        detail=None
        if r.get('detail_code') is not None:
            try:detail=D(r['detail_code'])
            except (ValueError,TypeError):raise DiagnosticError('invalid_presented_detail') from None
        label=LABELS[r['state']];message=DETAILS.get(detail,FALLBACK_TEXT.get(r['code'],'Sem evidência suficiente. Estado do componente não confirmado.'))
        verification='Verificado na simulação' if r['valid'] else 'Não confirmado'
        if r['valid'] and not report['simulation']:verification='Verificado em leitura passiva'
        if r['code'] in ERROR_CODES:
            label='Falha';message='Falha na verificação; o estado do componente não foi confirmado. Sem repetição ou reparo automático.'
        elif r['state']=='unknown' or r['code'] in PRIMARY_UNKNOWN:
            if not report['simulation']:label='Não verificado'
            verification='Não verificado'
            message='Evidência inconclusiva; não confirma indisponibilidade do PC.'
            if detail in (D.STARTUP_DISPATCH_UNCONFIRMED,D.STARTUP_NOT_VERIFIED,D.STARTUP_EXISTING_INSTANCE):message=DETAILS[detail]
        elif r['state']=='stale':message='A última evidência excedeu a validade. Não utilizar como estado atual.'
        cards.append({'component':component.value,'title':TITLES[component],'label':label,'raw_state':r['state'],
                      'verification':verification,'message':message,'code':r['code'],'detail_code':detail.value if detail else None,
                      'observed_at':r['observed_at'],'age_seconds':r['age_seconds'],
                      'last_communication':r['last_communication'],'evidence_kind':kind})
    result={'schema_version':1,'title':'Autodiagnóstico · '+('PRÉVIA SIMULADA' if report['simulation'] else 'LEITURA PASSIVA'),'simulation':report['simulation'],'read_only':True,
            'repair_capability':False,'generated_at':report['generated_at'],'cards':cards}
    if len(json.dumps(result).encode('utf-8'))>16384:raise DiagnosticError('diagnostic_view_limit')
    return result


def render_html(report):
    view=present(report)
    colors={'Saudável':'#91e0c2','Indisponível':'#b4b4c2','Desatualizado':'#ffd18a','Falha':'#ff6883'}
    cards=[]
    for c in view['cards']:
        last=c['last_communication'] or 'Nenhuma confirmada'
        age='Não disponível' if c['age_seconds'] is None else f"{c['age_seconds']:.3f} s"
        communication=f'<dt>Última comunicação autenticada</dt><dd>{escape(last)}</dd>' if c['component']==Component.HTTPS else ''
        cards.append(f'<article><h2>{escape(c["title"])}</h2><strong style="color:{colors[c["label"]]}">{escape(c["label"])}</strong><small>{escape(c["verification"])} · SIMULADO</small><p>{escape(c["message"])}</p><dl><dt>Horário da evidência</dt><dd>{escape(c["observed_at"] or "Não observado")}</dd><dt>Idade da evidência</dt><dd>{escape(age)}</dd>{communication}</dl></article>')
    return '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; connect-src \'none\'"><title>Autodiagnóstico · simulação</title><style>body{background:#0b0b0e;color:#f3f3f6;font:15px Segoe UI,Arial;margin:24px auto;padding:0 20px;max-width:1200px}h1{font-size:28px}header p{color:#c5b2bc;line-height:1.6}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}article{background:#151518;border:1px solid #2d2d35;border-radius:16px;padding:20px;min-width:0}h2{font-size:17px}strong{font-size:21px}small{display:block;color:#aaaab6;margin:12px 0}p{line-height:1.65;color:#c4c4cf}dl{font-size:12px;line-height:1.8}dt{color:#a5a5b1}dd{margin:0 0 8px;overflow-wrap:anywhere}.line{height:2px;background:#ff153f;width:60px}</style><header><h1>Autodiagnóstico · prévia simulada</h1><div class="line"></div><p>Fixtures locais. Nenhuma verificação real, conexão, reparo ou alteração nos aplicativos instalados. Indisponível não significa PC desligado.</p></header><section class="grid">'+''.join(cards)+'</section></html>'

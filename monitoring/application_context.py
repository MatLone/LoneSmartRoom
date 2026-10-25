"""Packaged sidecar context verification; no native construction on import."""
import os


def validate_mode(root,application,simulated):
    bundled=(root/'BUNDLED-MONITORING.json').is_file()
    if bundled and (not application or simulated):raise PermissionError('bundle_requires_real_application_mode')
    if application and not bundled:raise PermissionError('application_mode_requires_bundle')
    return bundled


def application_owner(api,root,owner_pid):
    expected_python=os.path.normcase(os.path.realpath(root.parent/'runtime/python.exe'))
    expected_owner=os.path.normcase(os.path.realpath(root.parents[2]/'Lone Smart Room.exe'))
    if api.own['image']!=expected_python or os.getppid()!=owner_pid:
        raise PermissionError('unexpected_application_context')
    handle=api.hold_process(owner_pid)
    try:
        identity=api.identity(handle)
        if not api.alive(handle) or identity['image']!=expected_owner or identity['elevated'] or any(identity[k]!=api.own[k] for k in ('sid','session')):
            raise PermissionError('unexpected_application_owner')
        return handle
    except Exception:
        api.close(handle);raise

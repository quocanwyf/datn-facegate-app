from app.api.contract import source_contract
from app.main import create_app

# Chỉ các operation được plan cho phép để T09/T11; không bỏ qua tùy ý theo tag.
DEFERRED={
    ('get','/me/today'),('get','/me/attendance'),('get','/me/days/{date}'),('get','/me/requests'),('post','/me/requests'),('post','/me/requests/{id}/cancel'),
    ('post','/gates/{id}/manual-open'),('get','/shifts'),('post','/shifts'),('patch','/shifts/{id}'),
    ('get','/shift-assignments'),('post','/shift-assignments'),('delete','/shift-assignments/{id}'),
    ('get','/holidays'),('post','/holidays'),('delete','/holidays/{date}'),
    ('get','/attendance/days'),('patch','/attendance/days/{id}'),('post','/attendance/leave'),('get','/attendance/export'),('post','/attendance/manual'),
    ('get','/attendance/requests'),('post','/attendance/requests/{id}/approve'),('post','/attendance/requests/{id}/reject'),
    ('get','/events'),('get','/events/{id}/snapshot'),('post','/events/{id}/handle'),('get','/events/manual-report'),('get','/events/export')}


def test_all_operations_in_scope_have_real_routes_and_canonical_contract():
    app=create_app();document=app.openapi();source=source_contract()
    def real_routes(routes,prefix=''):
        for route in routes:
            if hasattr(route,'original_router'):
                yield from real_routes(route.original_router.routes,prefix+route.include_context.prefix)
            elif hasattr(route,'methods'):
                for method in route.methods:yield method.lower(),prefix+route.path
    real=set(real_routes(app.routes))
    implemented=[]
    for path,operations in source['paths'].items():
        for method,operation in operations.items():
            if (method,path) in DEFERRED:continue
            full='/api/v1'+path
            assert (method,full) in real,(method,path,'thiếu route thật')
            assert document['paths'][full][method]['operationId']==operation['operationId']
            implemented.append((method,path))
    print(f'implemented_operations={len(implemented)}; deferred_T09_T11={len(DEFERRED)}')
    for method,path in sorted(DEFERRED):print('DEFERRED',method.upper(),path)

"""Kiểm kê caller trực tiếp và dependency FastAPI cho báo cáo rà soát T06."""
import argparse
import ast
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import create_app


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    names={'require_roles','current_user','find_device','manageable_user','withdraw_consent','review_profile','validate_roles','scoped','body_contract'}
    callers={name:[] for name in names};files=list((root/'app').rglob('*.py'))
    for path in files:
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if not isinstance(node,ast.Call):continue
            name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
            if name in callers:callers[name].append(f'app/{path.relative_to(root/"app").as_posix()}:{node.lineno}')
    dependencies={}
    def dependency_names(dependant):
        call=dependant.call
        if call:yield getattr(call,'__qualname__',type(call).__name__)
        for child in dependant.dependencies:yield from dependency_names(child)
    def routes(branch):
        for route in branch:
            if hasattr(route,'original_router'):yield from routes(route.original_router.routes)
            elif hasattr(route,'dependant'):yield route
    for route in routes(create_app().routes):
        for name in set(dependency_names(route.dependant)):
            dependencies.setdefault(name,[]).append(route.path)
    result={'python_app_files':len(files),'strategy':'MEDIUM/FOCUSED; auth/RBAC HIGH',
            'direct_syntactic_calls':callers,'fastapi_dependencies_by_route':dependencies,
            'limits':'Static counts are references, not dynamic execution counts or line coverage.'}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('app_files',len(files),'current_user_route_refs',len(dependencies.get('current_user',[])))


if __name__=='__main__':main()

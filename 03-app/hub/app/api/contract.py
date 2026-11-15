"""DTO kiểm từ OpenAPI gốc; không tin trường ngoài whitelist của operation."""
from copy import deepcopy
from functools import lru_cache
import math
from fastapi import Request
from jsonschema import Draft202012Validator, FormatChecker
import yaml
from app.config import ROOT
from app.errors import ApiError


@lru_cache
def source_contract():
    return yaml.safe_load((ROOT / '03-app/openapi/openapi.yaml').read_text(encoding='utf-8'))


def body_contract(name, status=400):
    schema={'$ref':'#/components/schemas/'+name,'components':source_contract()['components']}
    validator=Draft202012Validator(schema,format_checker=FormatChecker())
    async def dependency(request: Request) -> dict:
        try:
            data=await request.json()
        except ValueError:
            raise ApiError(status,'VALIDATION_ERROR','Dữ liệu JSON không hợp lệ.') from None
        def finite(value):
            if isinstance(value,float):return math.isfinite(value)
            if isinstance(value,dict):return all(finite(item) for item in value.values())
            if isinstance(value,list):return all(finite(item) for item in value)
            return True
        if not finite(data) or next(validator.iter_errors(data),None) is not None:
            # Không echo input mật khẩu/PIN hoặc đường dẫn file từ lỗi validator.
            raise ApiError(status,'VALIDATION_ERROR','Dữ liệu không hợp lệ theo hợp đồng API.')
        return data
    return dependency


def install_contract_docs(app):
    generated=app.openapi
    def openapi():
        if app.openapi_schema:
            return app.openapi_schema
        document=generated()
        source=source_contract()
        document.setdefault('components',{}).setdefault('schemas',{}).update(deepcopy(source['components']['schemas']))
        for section in ('responses','parameters','securitySchemes'):
            document['components'][section]=deepcopy(source['components'].get(section,{}))
        for path,operations in document['paths'].items():
            canonical=source['paths'].get(path.removeprefix('/api/v1'),{})
            for method in list(operations):
                if method in canonical:
                    operations[method]=deepcopy(canonical[method])
        app.openapi_schema=document
        return document
    app.openapi=openapi

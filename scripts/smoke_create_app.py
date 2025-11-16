from importlib import import_module

app_mod = import_module('app')
app = app_mod.create_app()
print('create_app ok')

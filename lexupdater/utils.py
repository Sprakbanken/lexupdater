#!/usr/bin/env python
# coding=utf-8

"""Extra utility functions that can be useful across the package"""


def get_module_variable_names(module_name):
    module = globals().get(module_name, None)
    module_variables = {}
    if module:
        module_variables = {
            key: value for key, value in module.__dict__.items()
            if not (key.startswith('__') or key.startswith('_'))
        }
    return module_variables


if __name__ == '__main__':
    import config

    module_variables = get_module_variable_names('config')
    print("CONFIG values")
    print("-"*13)
    for key, value in module_variables.items():
        print(f"{key: <20}{value}")

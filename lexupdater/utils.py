#!/usr/bin/env python
# coding=utf-8

"""Extra utility functions that can be useful across the package"""


def get_module_variable_names(module_name):
    """Extract only public, global variables from the given module_name.

    Parameters
    ----------
    module_name: str

    Returns
    -------
    dict
        keys are variable names and values are their assigned values
    """
    module = globals().get(module_name, None)
    module_variables = {}
    if module:
        module_variables = {
            var_name: var_value
            for var_name, var_value in module.__dict__.items()
            if not (var_name.startswith('__') or var_name.startswith('_'))
        }
    return module_variables


if __name__ == '__main__':

    module_vars = get_module_variable_names('config')
    print("CONFIG values")
    print("-"*13)
    for key, value in module_vars.items():
        print(f"{key: <20}{value}")


def models_to_str(instances):
    result_str = '\r\n'
    for instance in instances:
        result_str += '\r\n'
        for field, value in dict(instance).items():
            result_str += str(field) + ': ' + str(value) + '\r\n'
        result_str += '------------------------'
    return result_str


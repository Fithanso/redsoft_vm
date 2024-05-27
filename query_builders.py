
class WhereBuilder:

    @classmethod
    def build(cls, params, offset, mode):
        params_str = ''
        for item in enumerate(params.keys(), offset):
            num, key = item[0], item[1]

            params_str += str(key) + '=$' + str(num)
            if num != len(params.keys()) + offset - 1:
                params_str += f' {mode} '

        return params_str


class SetBuilder:

    @classmethod
    def build(cls, original_params, params_copy, offset):
        # needs to be refactored to correctly handle NULL value
        params_str = ''

        for item in enumerate(original_params.keys(), offset):
            num, key = item[0], item[1]
            params_str += str(key) + '='
            if original_params.get(key) == 'NULL' or original_params.get(key) == 'null':
                params_str += 'NULL'
                del params_copy[key]
            else:
                params_str += '$' + str(num)

            if num != len(original_params.keys()) + offset - 1:
                params_str += ', '

        return params_str, params_copy

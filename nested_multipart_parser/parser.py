import re


class NestedParser:
    _valid = None
    errors = None

    def __init__(self, data, options={}):
        self.data = data
        self._merge_options(options)

    def _merge_options(self, options):
        DEFAULT_OPTIONS = {
            "separator": "bracket",
            "raise_duplicate": True,
            "assign_duplicate": False
        }

        options = {**DEFAULT_OPTIONS, **options}
        self._options = options

        assert self._options.get("separator", "dot") in ["dot", "bracket"]
        assert isinstance(self._options.get("raise_duplicate", False), bool)
        assert isinstance(self._options.get("assign_duplicate", False), bool)

        self._is_dot = self._options["separator"] == "dot"
        if not self.is_dot:
            self._reg = re.compile(r"\[|\]")

    @property
    def is_dot(self):
        return self._is_dot

    def split_key(self, key):
        # remove space
        k = key.replace(" ", "")

        # remove empty string and count key length for check is a good format
        # reduce + filter are a hight cost so do manualy with for loop

        # optimize by split with string func
        if self.is_dot:
            length = 1
            splitter = k.split(".")
        else:
            splitter = self._reg.split(k)
            length = 2

        check = -length

        results = []
        for select in splitter:
            if select:
                results.append(select)
                check += len(select) + length

        if len(k) != check:
            raise Exception(f"invalid format from key {key}")
        return results

    def set_type(self, dtc, key, value, full_keys, prev=None, last=False):
        if isinstance(dtc, list):
            key = int(key)
            if len(dtc) < key:
                raise ValueError(
                    f"key \"{full_keys}\" is upper than actual list")
            if len(dtc) == key:
                dtc.append(value)
        elif isinstance(dtc, dict):
            if key not in dtc or self._options["assign_duplicate"] and last:
                dtc[key] = value
        else:
            if self._options["raise_duplicate"]:
                raise ValueError(
                    f"invalid rewrite key from \"{full_keys}\" to \"{dtc}\"")
            elif self._options["assign_duplicate"]:
                dtc = prev['dtc']
                dtc[prev['key']] = prev['type']
                return self.set_type(dtc[prev['key']], key, value, full_keys, prev, last)
        return key

    def get_next_type(self, keys):
        return [] if keys.isdigit() else {}

    def construct(self, data):
        dictionary = {}

        for key in data:
            keys = self.split_key(key)
            tmp = dictionary
            prev = {
                'key': keys[0],
                'dtc': tmp,
                'type': None
            }

            # optimize with while loop instend of for in with zip function
            i = 0
            lenght = len(keys) - 1
            while i < lenght:
                set_type = self.get_next_type(keys[i+1])
                index = self.set_type(
                    tmp, keys[i], set_type, key, prev=prev)
                prev['dtc'] = tmp
                prev['key'] = index
                prev['type'] = set_type
                tmp = tmp[index]
                i += 1

            self.set_type(tmp, keys[-1], data[key], key, prev=prev, last=True)
        return dictionary

    def is_valid(self):
        self._valid = False
        try:
            self.__validate_data = self.construct(self.data)
            self._valid = True
        except Exception as err:
            self.errors = err
        return self._valid

    @property
    def validate_data(self):
        if self._valid is None:
            raise ValueError(
                "You need to be call is_valid() before access validate_data")
        if self._valid is False:
            raise ValueError("You can't get validate data")
        return self.__validate_data

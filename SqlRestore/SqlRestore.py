import string
import sqlparse

class SqlRestore():
    SQL_START = "==>  Preparing: "
    SQL_END = "\n"
    PARAM_START = "==> Parameters: "
    PARAM_END = "\n"
    PARAM_STRING_TYPE = "String"
    PARAM_TIMESTAMP = "Timestamp"
    ADD_SINGLE_QUOTES_LIST = {PARAM_STRING_TYPE, PARAM_TIMESTAMP}
    REPLACE_REG = "?"
    SPLIT = ", "
    SINGLE_QUOTES = "'"

    def __init__(self):
        pass

    @staticmethod
    def restore(text: string):
        # print("执行sql还原方法" + text)
        if SqlRestore.SQL_START not in text:
            return text
        sql = text[text.index(SqlRestore.SQL_START) + len(SqlRestore.SQL_START):text.index(SqlRestore.SQL_END,
                                                                                           text.index(
                                                                                               SqlRestore.SQL_START) + len(
                                                                                               SqlRestore.SQL_START))]
        # print("sql is :" + sql)
        if SqlRestore.PARAM_START not in text:
            return sql
        param = text[text.index(SqlRestore.PARAM_START) + len(SqlRestore.PARAM_START):text.index(SqlRestore.PARAM_END,
                                                                                                 text.index(
                                                                                                     SqlRestore.PARAM_START) + len(
                                                                                                     SqlRestore.PARAM_START))]
        # print("param is :" + param)
        param_spit = param.split(SqlRestore.SPLIT)
        for paramTemp in param_spit:
            # print(paramTemp)
            if "(" in paramTemp:
                value = paramTemp[:paramTemp.index("(")]
                type = paramTemp[paramTemp.index("(") + 1: paramTemp.rindex(")")]
                # print(value)
                # print(type)
                if type in SqlRestore.ADD_SINGLE_QUOTES_LIST:
                    value = '\'' + value + '\''
                    pass
                sql = sql.replace(SqlRestore.REPLACE_REG, value, 1)
        return sqlparse.format(sql, reindent=True, keyword_case='upper')

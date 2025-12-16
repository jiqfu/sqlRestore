import sqlparse
import json
from typing import List, Tuple

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
    def restore(text: str) -> str:
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
        for value, param_type in SqlRestore._parse_parameters(param):
            sql = sql.replace(SqlRestore.REPLACE_REG, SqlRestore._format_value(value, param_type), 1)
        return sqlparse.format(sql, reindent=True, keyword_case='upper')

    @staticmethod
    def _parse_parameters(param_line: str) -> List[Tuple[str, str]]:
        """
        解析 MyBatis 日志中的 Parameters 行。

        典型格式：
          "1(Integer), {"a":1,"b":2}(String), null(Integer)"

        关键点：value 里可能包含大量逗号（如 JSON），因此不能简单按 ", " split。
        这里以 "(Type)" 作为参数项的可靠“结尾”标记：当遇到 ')' 且其后是 ", " 或字符串结束时，
        认为完成一个参数。
        """
        s = (param_line or "").strip()
        if not s:
            return []

        out: List[Tuple[str, str]] = []
        i = 0
        n = len(s)

        while i < n:
            # 跳过分隔符与空白
            if s.startswith(", ", i):
                i += 2
                continue
            while i < n and s[i].isspace():
                i += 1
            if i >= n:
                break

            j = i
            while True:
                open_idx = s.find("(", j)
                if open_idx == -1:
                    # 不符合预期格式，保底把剩余内容当作 value
                    tail = s[i:].strip()
                    if tail:
                        out.append((tail, ""))
                    i = n
                    break

                close_idx = s.find(")", open_idx + 1)
                if close_idx == -1:
                    tail = s[i:].strip()
                    if tail:
                        out.append((tail, ""))
                    i = n
                    break

                after = close_idx + 1
                # 只有当 ')' 后面是 ", " 或结束，才认为这是参数项的类型括号
                if after == n or s.startswith(", ", after):
                    value = s[i:open_idx].strip()
                    typ = s[open_idx + 1:close_idx].strip()
                    out.append((value, typ))
                    i = after
                    if i < n and s.startswith(", ", i):
                        i += 2
                    break

                # 这个 '(' 不是类型括号，继续向后找下一个
                j = open_idx + 1

        return out

    @staticmethod
    def _format_value(value: str, param_type: str) -> str:
        v = "" if value is None else str(value)
        t = "" if param_type is None else str(param_type)

        # MyBatis 常见的 null 输出：null(Integer) / null(String) 等
        if v.strip().lower() == "null":
            return "NULL"

        # String / Timestamp 等需要单引号，并对单引号做 SQL 逃逸
        if t in SqlRestore.ADD_SINGLE_QUOTES_LIST:
            # 针对 insert/update 中常见的大 JSON 字符串：去转义 + JSON 规范化输出
            if t == SqlRestore.PARAM_STRING_TYPE:
                v = SqlRestore._normalize_json_if_possible(v)
            escaped = v.replace("'", "''")
            return f"'{escaped}'"

        return v

    @staticmethod
    def _normalize_json_if_possible(raw: str) -> str:
        """
        JSON 基础能力：
        - 支持对已转义 JSON（如 {\\\"a\\\":1}）进行“去转义”
        - 支持对 JSON 进行规范化输出（默认压缩为单行，便于直接执行 SQL）

        若不是 JSON（或解析失败），原样返回。
        """
        s = "" if raw is None else str(raw).strip()
        if not s:
            return raw

        obj = SqlRestore._try_parse_json(s)
        if obj is None:
            return raw

        # 规范化：去掉多余空白、保留中文（ensure_ascii=False）
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _try_parse_json(s: str):
        """
        尝试把 s 解析为 JSON 对象：
        1) 直接当 JSON（以 { 或 [ 开头）
        2) 若失败，先把 s 当作“被转义的字符串内容”反转义，再尝试解析
        """
        txt = (s or "").strip()
        if not txt:
            return None

        # 1) 直接 JSON
        if txt[0] in "{[":
            try:
                return json.loads(txt)
            except Exception:
                pass

        # 2) 可能是被转义后的 JSON（例如：{\"a\":1} 或 {\\\"a\\\":1}）
        # 把 txt 当作 JSON 字符串字面量的内容，先解码出真实字符串，再尝试 json.loads。
        try:
            # 这里用 json.loads 解“字符串字面量”，需要先把反斜杠/引号转成合法 JSON 字符串
            decoded = json.loads('"' + txt.replace("\\", "\\\\").replace('"', '\\"') + '"')
        except Exception:
            return None

        decoded = (decoded or "").strip()
        if not decoded:
            return None

        if decoded[0] in "{[":
            try:
                return json.loads(decoded)
            except Exception:
                return None

        return None

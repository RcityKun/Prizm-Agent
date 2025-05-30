# SurrealQL 构造工具
class QueryBuilder:
    def __init__(self, table):
        self.table = table
        self.filters = []

    def where(self, condition):
        self.filters.append(condition)
        return self  # 支持链式调用

    def build_select(self):
        query = f"SELECT * FROM {self.table}"
        if self.filters:
            query += " WHERE " + " AND ".join(self.filters)
        return query

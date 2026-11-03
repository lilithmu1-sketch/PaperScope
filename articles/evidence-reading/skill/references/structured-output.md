# 已有claims输出契约时的草稿

保持原schema_version、source_ids及claims字段。每个claim的id、statement、kind、verdict和reasoning仍由阅读者根据原文填写。仅将evidence对象改为：

```json
{"source_id":"实际来源ID","block_id":"实际块号","span":[0,120]}
```

span可省略；它是Python Unicode字符位置的左闭右开区间，不是UTF-8字节或JavaScript UTF-16位置。不得使用不存在的块或越界范围。需要更精确的引文时，基于实际原文选择连续范围；不靠改写或模糊匹配使引文通过。

编译器生成claims.json及相邻的claims-compile-provenance.json，并拒绝覆盖。也可用--out指定全新目录。比较表与回答仍按用户格式输出；草稿和编译溯源不替代最终三个文件。kind=unknown时仍须verdict=insufficient；其他断言的证据与判断关系需要阅读者负责。

工具不自动评分，也不验证科学真伪。完整块作为quote可能增大输出文件；不把这种体积转移隐藏为成本下降，实际输出大小应记录。

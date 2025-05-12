import re


def is_valid_ua(ua):
    # 更宽松的 UA 验证规则
    pattern = re.compile(
        r"""
        ^Mozilla/(4\.0|5\.0)          # 必须以 Mozilla/4.0 或 5.0 开头
        \s+                          # 空格
        \(.*?\)                      # 操作系统信息
        \s+                          # 空格
        (AppleWebKit/|Gecko/|Trident/|Version/|Edge/)?  # 浏览器引擎或版本标识（可选）
        \d+(\.\d+)*                  # 至少一个版本号（小数部分可选）
        .*                           # 允许后续扩展信息
        $                            # 行尾
    """,
        re.VERBOSE,
    )
    return re.match(pattern, ua.strip()) is not None


def main():
    input_file = r"E:\Code\Python\My_Funcs\OAFuncs\oafuncs\oa_down\User_Agent-list-old.txt"
    output_file = r"E:\Code\Python\My_Funcs\OAFuncs\oafuncs\oa_down\User_Agent-list.txt"

    valid_uas = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and is_valid_ua(line):
                valid_uas.append(line)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_uas))

    print(f"[Linux 兼容模式] 有效UA已保存到 {output_file}，共 {len(valid_uas)} 条")


if __name__ == "__main__":
    main()

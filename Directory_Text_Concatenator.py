# ==============================================================================
# 工具名称: 目录文本文件合并工具 (Directory_Text_Concatenator.py)
# 作用说明: 遍历指定目录及其所有子目录下的文本文件，自动跳过常见的图像、音频、
#           视频、可执行文件、压缩包和文档等非文本文件类型。
#           它将所有识别为文本的文件内容拼接到一个单独的输出文件中，
#           并在每个文件内容前添加原始文件路径作为标记，方便内容溯源。
#           适合用于代码、日志、文档片段等纯文本内容的快速收集与整理。
#
# 适配Python版本: Python 3.6 及以上
# 依赖模块: 无
# ==============================================================================

import os

# 定义要跳过的文件扩展名列表
SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',   # 常见图像文件
    '.mp3', '.wav', '.aac', '.flac',   # 常见音频文件
    '.mp4', '.mkv', '.avi', '.mov',   # 常见视频文件
    '.exe', '.dll', '.so', '.o',   # 可执行文件和库
    '.zip', '.tar', '.gz', '.rar',   # 压缩文件
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',   # 文档格式（通常不是纯文本）
    '.sqlite', '.db',   # 数据库文件
    # 此处可以按格式添加
}


def concatenate_files_in_directory(root_dir, output_file_path):
    """
    遍历指定目录及其所有子目录下的文本文件，
    跳过指定的图像/二进制文件类型，
    将它们的内容拼接到一个输出文件中，并在每个文件内容前加上文件名。

    Args:
        root_dir (str): 要遍历的根目录路径。
        output_file_path (str): 输出的合并文本文件路径。
    """
    # 确保根目录存在
    if not os.path.isdir(root_dir):
        print(f"错误：目录 '{root_dir}' 不存在。")
        return

    # 确保输出文件路径不是输入目录的一部分
    abs_root_dir = os.path.abspath(root_dir)
    abs_output_file_path = os.path.abspath(output_file_path)

    if abs_output_file_path.startswith(abs_root_dir + os.sep) and \
            os.path.dirname(abs_output_file_path) == abs_root_dir:
        pass
    elif os.path.dirname(abs_output_file_path) == abs_root_dir and \
            os.path.basename(abs_output_file_path) != "":
        pass
    elif abs_output_file_path.startswith(abs_root_dir + os.sep):
        print(f"错误：输出文件 '{output_file_path}' 不能位于输入目录 '{root_dir}' 的深层子目录中，以避免递归问题。")
        print(f"建议将输出文件放在 '{root_dir}' 之外或其直接子目录（如果名称不冲突）。")
        return

    print(f"开始遍历目录：{abs_root_dir}")
    print(f"将内容写入到：{abs_output_file_path}")
    print(f"将跳过以下扩展名的文件：{', '.join(SKIP_EXTENSIONS)}")

    try:
        # 创建输出文件所在的目录（如果不存在）
        output_dir = os.path.dirname(abs_output_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"已创建输出目录：{output_dir}")

        with open(abs_output_file_path, 'w', encoding='utf-8') as outfile:
            file_count = 0
            skipped_count = 0
            for dirpath, dirnames, filenames in os.walk(abs_root_dir):
                if os.path.abspath(dirpath).startswith(os.path.dirname(abs_output_file_path)) and \
                        os.path.dirname(abs_output_file_path) != abs_root_dir and \
                        os.path.dirname(abs_output_file_path) != "":
                    if abs_output_file_path.startswith(os.path.abspath(dirpath)):
                        pass

                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)

                    # 避免读取输出文件自身
                    if os.path.abspath(file_path) == abs_output_file_path:
                        continue

                    # 检查文件扩展名
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in SKIP_EXTENSIONS:
                        print(f"  跳过文件 (扩展名不支持)：{file_path}")
                        skipped_count += 1
                        continue

                    try:
                        print(f"  正在处理文件：{file_path}")

                        header_marker = f"--- 文件开始：{filename} ---"
                        footer_marker = f"--- 文件结束：{filename} ---"

                        # 如果需要包含相对路径，取消注释下面两行，并注释上面两行
                        # relative_file_path = os.path.relpath(file_path, abs_root_dir)
                        # header_marker = f"--- 文件开始：{relative_file_path} ---"
                        # footer_marker = f"--- 文件结束：{relative_file_path} ---"

                        outfile.write(f"{header_marker}\n")

                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()
                            outfile.write(content)

                        outfile.write(f"\n{footer_marker}\n\n")
                        file_count += 1
                    except IOError as e:
                        error_file_identifier = os.path.relpath(file_path, abs_root_dir)
                        print(f"    警告：无法读取文件 '{file_path}'：{e}。已跳过。")
                        outfile.write(f"--- 错误：无法读取文件 {error_file_identifier}：{e} ---\n\n")
                        skipped_count += 1
                    except UnicodeDecodeError as e:
                        error_file_identifier = os.path.relpath(file_path, abs_root_dir)
                        print(f"    警告：文件 '{file_path}' 似乎不是纯文本文件 (解码失败)：{e}。已跳过。")
                        outfile.write(f"--- 错误：文件似乎不是纯文本 {error_file_identifier} (解码失败)：{e} ---\n\n")
                        skipped_count += 1
                    except Exception as e:
                        error_file_identifier = os.path.relpath(file_path, abs_root_dir)
                        print(f"    警告：处理文件 '{file_path}' 时发生未知错误：{e}。已跳过。")
                        outfile.write(f"--- 错误：处理文件 {error_file_identifier} 时发生未知错误：{e} ---\n\n")
                        skipped_count += 1

            print(f"\n处理完成！")
            print(f"总共拼接了 {file_count} 个文件到 '{abs_output_file_path}'。")
            if skipped_count > 0:
                print(f"总共跳过了 {skipped_count} 个文件。")


    except IOError as e:
        print(f"错误：无法写入到输出文件 '{abs_output_file_path}'：{e}")
    except PermissionError as e:
        print(f"错误：没有权限写入到输出文件 '{abs_output_file_path}'：{e}")
    except Exception as e:
        print(f"发生未知错误：{e}")


if __name__ == "__main__":
    # 提示用户输入或直接在此处修改变量
    print("--- 文件内容合并脚本 ---")

    # 方式一：让用户输入路径
    source_directory = input("请输入要遍历的源目录路径：").strip()
    output_file = input("请输入合并后的输出文件路径 (例如 output/combined.txt 或 ../all_texts.txt)：").strip()

    # 方式二：直接在脚本中指定路径 (如果使用此方式，请注释掉上面的 input 行)
    # 示例如下：
    # source_directory = "C:/Users/YourName/Documents/SourceCode"
    # output_file = "C:/Users/YourName/Documents/CombinedOutput.txt"

    if not source_directory:
        print("错误：未提供源目录路径。")
    elif not output_file:
        print("错误：未提供输出文件路径。")
    else:
        concatenate_files_in_directory(source_directory, output_file)
        print(f"\n脚本执行完毕。如果成功，请查看合并后的文件：{os.path.abspath(output_file)}")
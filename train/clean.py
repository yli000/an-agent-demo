import os

import glob


print("🧹 正在全盘扫描残留的缓存文件...")


# 1. 扫描所有 .pkl 文件 (缓存通常是这个后缀)

pkl_files = glob.glob('**/*.pkl', recursive=True)


deleted_count = 0

for file in pkl_files:

    # 过滤掉 miniconda 环境里的文件，只删项目里的

    if "miniconda" in file or "site-packages" in file:

        continue


    try:

        os.remove(file)

        print(f"✅ 已删除缓存: {file}")

        deleted_count += 1

    except Exception as e:

        print(f"❌ 删除失败 {file}: {e}")


if deleted_count == 0:

    print("⚠️ 未发现显式 .pkl 缓存。检查是否有其他后缀...")

else:

    print(f"🎉 清理完毕！共删除了 {deleted_count} 个缓存文件。")


# 2. 强制清空 saved/intent 下的旧模型

import shutil

if os.path.exists("saved/intent"):

    shutil.rmtree("saved/intent")

    print("✅ 已清空 saved/intent/ 目录，防止加载旧权重。")

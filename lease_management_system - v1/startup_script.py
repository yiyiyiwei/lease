#!/usr/bin/env python3
"""
租赁合同管理系统启动脚本
自动检查依赖并启动系统
"""
import sys
import subprocess
import importlib
import os
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 9):
        print("错误：需要Python 3.9或更高版本")
        print(f"当前Python版本：{sys.version}")
        return False
    return True

def check_and_install_dependencies():
    """检查并安装依赖包"""
    required_packages = {
        'tkinter': 'tkinter',
        'tkcalendar': 'tkcalendar==1.6.1',
        'pandas': 'pandas>=1.5.0',
        'openpyxl': 'openpyxl>=3.0.10'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            importlib.import_module(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"✗ {package} 未安装")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"\n发现缺少的依赖包：{', '.join(missing_packages)}")
        response = input("是否自动安装？(y/n): ").lower().strip()
        
        if response == 'y':
            for package in missing_packages:
                print(f"正在安装 {package}...")
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                    print(f"✓ {package} 安装成功")
                except subprocess.CalledProcessError:
                    print(f"✗ {package} 安装失败")
                    return False
        else:
            print("请手动安装依赖包：pip install -r requirements.txt")
            return False
    
    return True

def check_file_structure():
    """检查必要的文件结构"""
    required_dirs = [
        'config', 'database', 'models', 'services', 
        'ui', 'ui/dialogs', 'lease_accounting', 'utils'
    ]
    
    required_files = [
        'main.py',
        'config/settings.py',
        'database/manager.py',
        'models/entities.py',
        'services/contract_service.py',
        'services/payment_service.py',
        'ui/main_window.py',
        'lease_accounting/core.py',
        'utils/logging.py'
    ]
    
    missing_items = []
    
    # 检查目录
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_items.append(f"目录: {dir_path}")
    
    # 检查文件
    for file_path in required_files:
        if not os.path.isfile(file_path):
            missing_items.append(f"文件: {file_path}")
    
    if missing_items:
        print("缺少必要的文件或目录：")
        for item in missing_items:
            print(f"  ✗ {item}")
        return False
    
    print("✓ 文件结构检查通过")
    return True

def create_initial_directories():
    """创建初始目录"""
    dirs_to_create = ['logs', 'backups']
    
    for dir_name in dirs_to_create:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✓ 创建目录: {dir_name}")

def main():
    """主启动函数"""
    print("="*50)
    print("租赁合同管理系统启动检查")
    print("="*50)
    
    # 检查Python版本
    if not check_python_version():
        input("按回车键退出...")
        sys.exit(1)
    
    # 检查文件结构
    if not check_file_structure():
        print("\n文件结构不完整，请检查系统安装")
        input("按回车键退出...")
        sys.exit(1)
    
    # 检查并安装依赖
    if not check_and_install_dependencies():
        print("\n依赖包安装失败，请手动安装")
        input("按回车键退出...")
        sys.exit(1)
    
    # 创建必要目录
    create_initial_directories()
    
    print("\n" + "="*50)
    print("系统检查完成，正在启动...")
    print("="*50)
    
    try:
        # 导入并运行主程序
        from main import main as main_app
        main_app()
    except Exception as e:
        print(f"\n启动失败：{str(e)}")
        print("\n请检查错误信息并重试")
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()

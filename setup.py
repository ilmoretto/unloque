from setuptools import setup, find_packages

setup(
    name="unloque",
    version="0.1.0",
    description="Ferramenta modular de recuperação, auditoria e geração contextual de senhas ZIP",
    author="Unloque Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask>=3.0.0",
        "pyzipper>=0.3.6",
    ],
    entry_points={
        "console_scripts": [
            "unloque=unloque.main:main",
        ],
    },
    python_requires=">=3.8",
)

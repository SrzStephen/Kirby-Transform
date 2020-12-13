clean:
 pip3 install isort autoflake; \
 isort src; \
 isort test; \
 autoflake --in-place --recursive src;

remove-unused-unsafe:
    pip3 install autoflake; \
    autoflake --in-place --recursive --remove-all-unused-imports --remove-duplicate-keys --remove-unused-variables
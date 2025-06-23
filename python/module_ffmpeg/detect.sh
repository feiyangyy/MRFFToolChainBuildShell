#!/usr/bin/env bash

# 初始化一个关联数组来存储每个库的信息
declare -A results

# 定义检查函数
check_library() {
    local lib_name=$1
    local enable_flag=$2
    local disable_flag=$3
    local version_cmd=$4

    if pkg-config --libs "$lib_name" --silence-errors >/dev/null; then
        local version=$($version_cmd)
        results["$lib_name"]="{\"enabled\": true, \"flags\": \"$enable_flag\", \"version\": \"$version\"}"
    else
        results["$lib_name"]="{\"enabled\": false, \"flags\": \"$disable_flag\", \"version\": \"\"}"
    fi
}

# 检查 openssl
check_library "openssl" "--enable-nonfree --enable-openssl" "--disable-openssl" "pkg-config --modversion openssl"

# 检查 opus
check_library "opus" "--enable-libopus --enable-decoder=opus" "--disable-libopus --disable-decoder=opus" "pkg-config --modversion opus"

# 检查 dav1d
check_library "dav1d" "--enable-libdav1d --enable-decoder=libdav1d" "--disable-libdav1d --disable-decoder=libdav1d" "pkg-config --modversion dav1d"

# 检查 libsmb2
check_library "libsmb2" "--enable-libsmb2 --enable-protocol=libsmb2" "--disable-libsmb2 --disable-protocol=libsmb2" "pkg-config --modversion libsmb2"

# 检查 libbluray
check_library "libbluray" "--enable-libbluray --enable-protocol=bluray" "--disable-libbluray --disable-protocol=bluray" "pkg-config --modversion libbluray"

# 检查 dvdread
check_library "dvdread" "--enable-libdvdread --enable-protocol=dvd" "--disable-libdvdread --disable-protocol=dvd" "pkg-config --modversion dvdread"

# 检查 uavs3d
check_library "uavs3d" "--enable-libuavs3d --enable-decoder=libuavs3d" "--disable-libuavs3d --disable-decoder=libuavs3d" "pkg-config --modversion uavs3d"

# 检查 libxml-2.0
check_library "libxml-2.0" "--enable-demuxer=dash --enable-libxml2" "--disable-demuxer=dash --disable-libxml2" "pkg-config --modversion libxml-2.0"

check_library "avc" "--enable-demuxer=dash --enable-libxml2" "--disable-demuxer=dash --disable-libxml2" "pkg-config --modversion libxml-2.0"
# 处理 av3a
# results["av3a"]="{\"enabled\": true, \"flags\": \"--enable-parser=av3a --enable-demuxer=av3a\", \"version\": \"\"}"

# 构建 JSON 输出
json_output="{"
first=true
for key in "${!results[@]}"; do
    if [ "$first" = true ]; then
        first=false
    else
        json_output+=","
    fi
    json_output+="\"$key\": ${results[$key]}"
done
json_output+="}"

# 输出格式化后的 JSON
echo "$json_output" | jq .
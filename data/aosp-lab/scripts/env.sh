#!/usr/bin/env bash

# Source this file before repo/build/emulator commands.

export AOSP_LAB_ROOT=/home/taejin/Jupyter/data/aosp-lab
export AOSP_SOURCE_ROOT="$AOSP_LAB_ROOT/source"
export AOSP_OUT_DIR="$AOSP_LAB_ROOT/out"
export AOSP_DIST_DIR="$AOSP_LAB_ROOT/dist"
export AOSP_LOG_DIR="$AOSP_LAB_ROOT/logs"
export ANDROID_SDK_ROOT=/home/taejin/Jupyter/data/android-emulator/sdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$HOME/bin:$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/emulator:$PATH"

mkdir -p \
  "$AOSP_LAB_ROOT/artifacts" \
  "$AOSP_LAB_ROOT/cache" \
  "$AOSP_LAB_ROOT/configs" \
  "$AOSP_LAB_ROOT/dist" \
  "$AOSP_LAB_ROOT/docs" \
  "$AOSP_LAB_ROOT/logs" \
  "$AOSP_LAB_ROOT/out" \
  "$AOSP_SOURCE_ROOT"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from plugin.base import FontPlugin


class MSYHPlugin(FontPlugin):
    """微软雅黑字体处理插件"""
    
    font_name = "msyh"
    font_name_display = "微软雅黑"
    backup_dir_name = "backup/msyh"
    fake_font_dir_name = "fake-font/msyh"
    file_pattern = "msyh*"
    source_files = ["MicrosoftYaHei", "MicrosoftYaHeiUI", "MicrosoftYaHeiLight", "MicrosoftYaHeiUILight", "MicrosoftYaHei-Bold", "MicrosoftYaHeiUI-Bold"]
    output_files = ["msyh.ttc", "msyhl.ttc", "msyhbd.ttc"]
    registry_entries = [
        "Microsoft Yahei & Microsoft Yahei UI (TrueType)",
        "Microsoft Yahei Bold & Microsoft Yahei UI Bold (TrueType)",
        "Microsoft Yahei Light & Microsoft Yahei UI Light (TrueType)",
    ]
    name_table_files = [
        "MicrosoftYaHei.ttx",
        "MicrosoftYaHeiUI.ttx",
        "MicrosoftYaHeiLight.ttx",
        "MicrosoftYaHeiUILight.ttx",
        "MicrosoftYaHei-Bold.ttx",
        "MicrosoftYaHeiUI-Bold.ttx",
    ]
    required_fake_files = ["Regular.ttf", "Light.ttf", "Bold.ttf"]
    ttc_files = ["msyh.ttc", "msyhl.ttc", "msyhbd.ttc"]
    name_table_mapping = {
        "MicrosoftYaHei.ttf": "Regular.ttf",
        "MicrosoftYaHeiUI.ttf": "Regular.ttf",
        "MicrosoftYaHeiLight.ttf": "Light.ttf",
        "MicrosoftYaHeiUILight.ttf": "Light.ttf",
        "MicrosoftYaHei-Bold.ttf": "Bold.ttf",
        "MicrosoftYaHeiUI-Bold.ttf": "Bold.ttf",
    }
    ttc_files_dict = {
        "msyh.ttc": ["MicrosoftYaHei.ttf", "MicrosoftYaHeiUI.ttf"],
        "msyhl.ttc": ["MicrosoftYaHeiLight.ttf", "MicrosoftYaHeiUILight.ttf"],
        "msyhbd.ttc": ["MicrosoftYaHei-Bold.ttf", "MicrosoftYaHeiUI-Bold.ttf"],
    }
    registry_entries_dict = {
        "Microsoft Yahei & Microsoft Yahei UI (TrueType)": "msyh.ttc",
        "Microsoft Yahei Bold & Microsoft Yahei UI Bold (TrueType)": "msyhbd.ttc",
        "Microsoft Yahei Light & Microsoft Yahei UI Light (TrueType)": "msyhl.ttc",
    }

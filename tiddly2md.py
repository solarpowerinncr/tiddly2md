#!/bin/env python
# coding: utf-8

from __future__ import print_function
import argparse
import re
import os
import unicodedata
import sys

import pandas as pd


def good_tag(tag, valid_tags):
    """Returns True if tag contains of the valid tags.

    :param tag: string
    :param valid_tags: list of valid tags
    """
    for each in valid_tags:
        if each in str(tag):
            return True
    return False


def wiki_to_md(text):
    """Convert wiki formatting to markdown formatting.

    :param text: string of text to process

    :return: processed string
    """
    fn = []
    new_text = []
    fn_n = 1  # Counter for footnotes
    for line in text.split('\n'):
        # lists (unordered, ordered and mixed)
        # 三部分分别匹配符号、空格、内容
        match = re.match("^([#\*]+)(\s*)(.*)", line)
        if match:
            list, additional_space, text = match.groups()
            # wikitext根据符号个数缩进
            num_of_spaces = 4 * (len(list) - 1)
            spaces = " " * num_of_spaces
            list_type = ""
            # 转换成数列或点列
            if list[-1] == "#":
                list_type = "1. "
            else:
                list_type = "* "
            line = spaces + list_type + text
        # Replace wiki headers with markdown headers
        match = re.match('(!+)(\\s?)[^\\[]', line)
        if match:
            header, spaces = match.groups()
            new_str = '#' * len(header)
            line = re.sub('(!+)(\\s?)([^\\[])', new_str + ' ' + '\\3', line)
        # Underline (doesn't exist in MD)
        line = re.sub("__(.*?)__", "\\1", line)
        # Bold
        line = re.sub("''(.*?)''", "**\\1**", line)
        # Italics
        line = re.sub("//(.*?)//", "_\\1_", line)
        # Remove wiki links
        line = re.sub("\\[\\[(\\w+?)\\]\\]", "\\1", line)
        # Change links to markdown format
        line = re.sub("\\[\\[(.*)\\|(.*)\\]\\]", "[\\1](\\2)", line)
        # Code
        line = re.sub("\\{\\{\\{(.*?)\\}\\}\\}", "`\\1`", line)
        # Footnotes
        match = re.search("```(.*)```", line)
        if match:
            text = match.groups()[0]
            fn.append(text)
            line = re.sub("```(.*)```", '[^{}]'.format(fn_n), line)
            fn_n += 1
        new_text.append(line)

    # Append footnotes
    for i, each in enumerate(fn):
        new_text.append('[^{}]: {}'.format(i+1, each))
    return '\n'.join(new_text)


def sanitize(value):
    """Makes sure filenames are valid by replacing illegal characters

    :param value: string
    """
    value = str(value)
    value = unicodedata.normalize('NFKD', value)
    value = str(re.sub('[^\w\s-]', '', value).strip())
    return value


def main(args):

    output_path = args.outdir
    try:
        os.mkdir(output_path)
    except OSError:
        pass

    # 读取csv时,空白项读取为空字符串
    df = pd.read_csv(args.input_file,na_values=str,keep_default_na=False)
    if args.tags:
        df = df[df.tags.apply(lambda x: good_tag(x, args.tags))]

    for row_id, row in df.iterrows():
        filename = sanitize(row.title)
        filename = '{}.{}'.format(filename, args.ext)
        with open(os.path.join(output_path, filename), 'w') as f:
            try:
                # 当条目类型为空或tw5时才进行转换
                if (len(row.type) == 0 or row.type == 'text/vnd.tiddlywiki'):
                    f.write(wiki_to_md(row.text))
                else:
                    f.write(row.text)
            except:
                f.write('')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Convert TiddlyWiki tiddlers exported as CSV to "
                    "individual files.")
    parser.add_argument('--ext', '-e', dest='ext',
                        default='md',
                        help='File extension (defaults to "md")')
    parser.add_argument('--outdir', '-o',
                        default='output',
                        dest='outdir',
                        help='Output folder (defaults to "output")')
    parser.add_argument('--tags', '-t', dest='tags',
                        action='append',
                        help='Valid tag to export, can have multiple')
    parser.add_argument('input_file',
                        help='Exported CSV file')
    args = parser.parse_args()

    sys.exit(main(args))

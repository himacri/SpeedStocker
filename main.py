# ------------------------------------------------------------------
#
#   login.py
#
#                   Nov/07/2018
#
# ------------------------------------------------------------------
from flask import Flask
from flask import Flask,flash,redirect,render_template,request,session,abort
from flask import Flask, request, Response, abort, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from collections import defaultdict
import os
import sys
import pandas as pd
from flask import Flask, request, url_for, make_response
from flask import render_template
from werkzeug.datastructures import FileStorage
from bs4 import BeautifulSoup
import io, pkgutil
# Seleniumを使用するのに必要なライブラリをダウンロード
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import chromedriver_binary
import time,os,sys,random,re,csv,lxml
from xml.dom.minidom import parse, parseString
from werkzeug.utils import secure_filename
from markupsafe import escape
import csv

# ドライバーをUIなしで使用するための設定
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver',options=options)
driver.implicitly_wait(0.1)

pd.options.display.max_columns = None
pd.set_option('display.max_columns', None)
pd.options.display.notebook_repr_html = True

class MyClass:
    itemList_df = []
    list1 = []
    columns1 = ["item_id"]

    deletelist_df = pd.DataFrame(data=list1, columns=columns1)
    New_df = []

class User(UserMixin):
    def __init__(self, id, name, password):
        self.id = id
        self.name = name
        self.password = password

# ログイン用ユーザー作成
users = {
    1: User(1, "user01", "01pas"),
    2: User(2, "user02", "password"),
    3: User(3, "himacri", "19732684"),
}

# ユーザーチェックに使用する辞書作成
nested_dict = lambda: defaultdict(nested_dict)
user_check = nested_dict()
for i in users.values():
    user_check[i.name]["password"] = i.password
    user_check[i.name]["id"] = i.id

global df

# ------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'hogehoge'

# ------------------------------------------------------------------
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        str_out = ""
        str_out += "<h2>こんにちは</h2>"
        str_out +=  "Hello Boss!<p />"
        str_out += "<a href='/logout'>Logout</a><br />"
#
        return str_out

# ------------------------------------------------------------------
@app.route('/login', methods=['POST'])
def do_admin_login():
    if(request.form["username"] in user_check and request.form["password"] == user_check[request.form["username"]]["password"]):
        session['logged_in'] = True
        return render_template('uploads.html')
    else:
        flash('wrong password!')
    return home()

# ------------------------------------------------------------------
@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

# ------------------------------------------------------------------
@app.route('/uploads', methods=['POST', 'GET'])
def check_zaiko():

    if request.method == 'POST':
        # ファイル選択
        csv_data = request.files["the_file"]
        # csvファイルのみ受け付ける
        if isinstance(csv_data, FileStorage) and csv_data.content_type == 'text/csv' :

            # データ整理 ここから
            # DataFlame:dfに代入 itemIDとSKUの2列だけ取得
            df = pd.read_csv(csv_data, usecols=[0, 1])
            # 3列目URLを追加
            for i in df.index :
                # 追加要素 SKUのurl
                url = ("https://www.mercari.com/jp/items/" + str(df.values[i, 1]) + "/")
                df.loc[i, 'URL'] = url
            # 現状dfを表示
            #print(df)
            # データ整理 ここまで
            # ID,SKU,URLを用意できた

            # スクレイピングする ここから

            i = 1
            ii = 1

            # アクセスするURL
            for index_name, item in df.iterrows() :
                url = ("https://www.mercari.com/jp/items/" + str(item[1]) + "/")
                # 指定したURLに遷移
                driver.get(url)
                resp = driver.page_source.encode('utf-8')

                if not url == "https://www.mercari.com/jp/items/No_sku/" \
                        and not url == "https://www.mercari.com/jp/items/nan/" :
                    soup = BeautifulSoup(resp, 'html.parser')
                    print(url)
                    try :  # 1-商品が削除されていないかの判定を、価格があるかどうかで調べる
                        # 価格
                        driver.find_element_by_css_selector(
                            '.item-price.bold')
                        div = soup.find('div',
                                        class_="item-price-box text-center")
                        div.find('span', class_='item-price bold')

                        try :  # 2-さらに、売り切れボタンが設定されているか判定
                            driver.find_element_by_css_selector(
                                ".item-buy-btn.disabled")
                            div2 = soup.find('div',
                                             class_="item-buy-btn disabled")
                            # var.set(div2.string)#var.set("売り切れました")
                            MyClass.deletelist_df.loc[ii] = item[0]
                            i = i + 1
                            ii = ii + 1

                        except :  # 2-売り切れてなければ"在庫あります"と表示
                            # var.set("在庫あります")
                            i = i + 1

                    except NoSuchElementException :  # 1-価格がなければ削除されているので"売り切れました"と表示
                        '''
                        h2 = soup.find('h2',
                                       class_="deleted-item-name")
                                       '''
                        # var.set("売り切れました")
                        MyClass.deletelist_df.loc[ii] = item[0]
                        i = i + 1
                        ii = ii + 1

                else :
                    # var.set("skuはありません")
                    i = i + 1

            # スクレイピングする ここまで
            print(MyClass.deletelist_df)

            header = ['Item ID', 'Custom Label_SKU','URL']  # DataFrameのカラム名の1次元配列のリスト
            header = ['Item ID']  # DataFrameのカラム名の1次元配列のリスト
            #Item ID
            record = MyClass.deletelist_df.values.tolist()
            #url = MyClass.deletelist_df.values[:,1].tolist()
            #print(df)
            return render_template('finished.html',header=header, record=record)
        else:
            return render_template('finished.html',df="no way")

@app.route('/downloads', methods=['POST', 'GET'])
def write_csv() :
            #csvを保存
            resp = make_response(MyClass.deletelist_df.to_csv())
            resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
            resp.headers["Content-Type"] = "text/csv"
            render_template('finished.html',df=MyClass.deletelist_df)
            # csvをダウンロード
            return resp

# ------------------------------------------------------------------
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=False,host='0.0.0.0', port=4000)
# ------------------------------------------------------------------
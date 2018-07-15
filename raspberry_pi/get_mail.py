# -*- coding:utf-8 -*-

import imaplib
import email
import time

import email
from imaplib import IMAP4_SSL
from email.header import decode_header

if __name__ == '__main__':
    user = "*@gmail.com"
    FLOM = "*396@gmail.com"
    password = "*"

    imap_host = 'imap.gmail.com'       # GMailの場合
    imap_port = 993                    # GMailの場合
 
    try:
        conn = IMAP4_SSL(imap_host, imap_port)
        conn.login(user, password)
 
        num = conn.select(mailbox='INBOX', readonly=True)     # readonly=False で受信後に既読
 
        # typ, data = conn.search(None, 'ALL')     # 全メール
        typ, data = conn.search(None, '(UNSEEN HEADER FROM %s)' % FLOM)     # 未読のみ
        ids = data[0].split()

        # Search from backwards
        for mid in ids[::-1]:
            typ, data = conn.fetch(mid, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
 
            header = decode_header(msg.get('Subject'))
            msg_subject  = header[0][0]
            msg_encoding = header[0][1] or 'iso-2022-jp'
 
            if msg.is_multipart() == False:  # シングルパート
                byt  = bytearray(msg.get_payload(), msg_encoding)
                body = byt.decode(encoding=msg_encoding)
            else: # マルチパート
                prt  = msg.get_payload()[0]
                byt  = prt.get_payload(decode=True)
                body = byt.decode(encoding=msg_encoding)
 
            print('from_address=' + str(msg.get('From')))
            print('to_addresses=' + str(msg.get('To')))
            print('cc_addresses=' + str(msg.get('CC')))
            print('bcc_addresses=' + str(msg.get('BCC')))
            print('date=' + str(msg.get('Date')))
            print('subject=' + str(msg_subject.decode(msg_encoding)))
            print('body=' + body)
            print('---------------------------------')
 
    except:
        raise
    finally:
        conn.close()
        conn.logout()


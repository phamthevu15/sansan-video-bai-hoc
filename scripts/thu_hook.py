"""Thử luật xuống dòng câu trích dẫn hook trên cả một bộ kịch bản (+3 hook cũ).

Chạy: python thu_hook.py <bo_kich_ban.json>           -> in cách xếp dòng của mọi hook
      python thu_hook.py <bo_kich_ban.json> 13 38     -> kèm từ loại pyvi của các hook đó (để dò vì sao ngắt sai)
bo_kich_ban.json: danh sách phần tử có trường `tts` (lời đọc Vbee, câu đầu = hook).
Sau mỗi lần sửa luật ngắt trong plan.py, chạy lại và so với lần trước."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan
if len(sys.argv) < 2:
    sys.exit(__doc__)
d=json.load(open(sys.argv[1],encoding='utf-8-sig'))
hooks=[re.split(r'(?<=[.!?])\s',re.sub(r'<break[^>]*>','',x['tts']).strip())[0] for x in d]
hooks+=['Có những câu trả lời về chính mình chỉ xuất hiện khi bạn bắt đầu làm.','Đừng chậm trễ với việc cần làm, cũng đừng nóng vội với điều đáng chờ.','Trí thông minh giúp bạn bắt đầu nhưng tính cách được rèn qua gian khó mới đưa bạn đi xa.']
sel=[int(a) for a in sys.argv[2:]] or range(1,len(hooks)+1)
for i in sel:
    hk=hooks[i-1]
    if len(sys.argv)>2:
        b=re.sub(r'[.!…]+$','',hk).split(); print(list(zip(b,plan.pos_tags([w.lower() for w in b]))))
    h=plan.make_headline(hk)
    print('%02d'%i, len(h['lines']), ' / '.join(h['lines']))

import fitz#pymupdf
from AI import askAI , rm_think 
import json

class PDFParser:
    def __init__(self, pdf_path: str):
        """
        初始化PDF解析器
        :param pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path        
        # 读取pdf,返回res,pic,page_num 
        self.res , self.pic ,self.page_num = self.read_pdf()
        self.set_type()
        
        
        #按页存储全部原始pdf内容
        self.pages = []
        for page in fitz.open(self.pdf_path):
            text = page.get_text('dict')
            self.pages.append(text)
        
        
        # AI识别的，暂不需要
        # 公文文种标记
        # 0: 未识别/其他 ,1: 函,2: 通知,3: 请示,4: 报告,5: 批复,6: 纪要,7: 通报,8: 决定
        # print("step：通过AI分析公文类型...",end='')
        # self.type = self.analyze_type()
        # print(f"成功: {self.type}")
        
        # print("step：通过AI提取公文文本...",end='')        
        # self.text = self.extract_text()
        # print(f"成功.\n{self.text}")

    def read_pdf(self):
        '''dhl
        读取pdf
        返回: (res,pic,page_num)
        res: 文本内容
        pic: 图片内容
        page_num: 页数
        '''
        f = fitz.open(self.pdf_path)
        res = []
        pic = []
        page_num = 0
        for page in f:
            page_num += 1
            text = json.loads(page.get_text("json"))
            # print(type(text))
            blocks = text["blocks"]
            blocks.sort(key = lambda x: x["bbox"][1])
            # print(blocks)
            # print("--------------------------------------------------------")
            for block in blocks:
                tmp = {}
                tmp["page"] = page_num
                tmp["bbox"] = block["bbox"]
                if block["type"] == 0:
                    tmp["text"] = ""
                    tmp["size"] = block["lines"][0]["spans"][0]["size"]
                    tmp["font"] = block["lines"][0]["spans"][0]["font"]
                    tmp["color"] = block["lines"][0]["spans"][0]["color"]
                    tmp["bbox"] = block["lines"][0]["spans"][0]["bbox"]
                    
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if (tmp["color"] != 0)and(span["color"] == 0):
                                tmp["color"] = 0
                            if span['color'] == 0:
                                tmp["text"] += span["text"]
                        

                    tmp["text"] = tmp["text"].strip()
                    res.append(tmp)
                elif block["type"] == 1:
                    tmp["width"] = block["width"]
                    tmp["height"] = block["height"]
                    tmp["ext"] = block["ext"]
                    pic.append(tmp)
                    
        return res , pic , page_num

    def set_type(self):
        types = {
            "title": 0,     #标题
            "title_1": 0,   #一级标题
            "title_2": 0,   #二级标题
            "title_3": 0,   #三级标题
            "title_4": 0,   #四级标题
            "text": 0,      #正文
            "page_num": 0,  #页码
            "stamp": 0,     #印章
            "addons": 0,    #附件说明
            "org": 0,       #单位
            "date": 0,      #日期
            "contact": 0,   #联系方式
            "note": 0,      #版记
            "others": 0     #其他
        }
        num_zh = "零一二三四五六七八九十百千万"
        num = "0123456789"
        for i in range(len(self.pic)):
            if (self.pic[i]["width"]/self.pic[i]["height"] < 1.1)and(self.pic[i]["height"]/self.pic[i]["width"] < 1.1)and(self.pic[i]["page"] == self.page_num):
                self.pic[i]["type"] = "stamp"
                types["stamp"] += 1
                stamp = self.pic[i]["bbox"]
            else:
                self.pic[i]["type"] = "others"
        # print(pic)
        l = len(self.res)
        for i in range(l): #忽略不是黑色的文字
            if self.res[i]["color"] != 0:
                self.res[i]["type"] = "others"
                types["others"] += 1
                continue
            if (self.res[i]["size"] > 20)and(self.res[i]["page"] == 1): #标题
                self.res[i]["type"] = "title"
                types["title"] += 1
                continue
            if ((i == l-1)or(self.res[i]["page"] < self.res[i+1]["page"]))and(len(self.res[i]["text"]) < 10): #页码
                flag = False
                for j in self.res[i]["text"]:
                    if j in num:
                        flag = True
                if flag:
                    self.res[i]["type"] = "page_num"
                    types["page_num"] += 1
                    continue
            if ((self.res[i]["page"] == self.page_num)
                and(self.res[i]["bbox"][0]+self.res[i]["bbox"][2] < stamp[2]*2)
                and(self.res[i]["bbox"][0]+self.res[i]["bbox"][2] > stamp[0]*2)
                and(self.res[i]["bbox"][1]+self.res[i]["bbox"][3] < stamp[3]*2)
                and(self.res[i]["bbox"][1]+self.res[i]["bbox"][3] > stamp[1]*2)):
                if ("年" in self.res[i]["text"])and("月" in self.res[i]["text"])and("日" in self.res[i]["text"]): #单位、日期
                    self.res[i]["type"] = "date"
                    types["date"] += 1
                    continue
                else:
                    self.res[i]["type"] = "org"
                    types["org"] += 1
                    continue
            if ((self.res[i]["text"][:3] == "附件：")or(types["addons"] > 0))and(types["org"] == 0)and(types["date"] == 0): #附件说明
                self.res[i]["type"] = "addons"
                types["addons"] += 1
                continue
            if ("、" in self.res[i]["text"]): #一级标题
                flag = True
                for j in self.res[i]["text"].split("、")[0]:
                    if not j in num_zh:
                        flag = False
                if flag:
                    self.res[i]["type"] = "title_1"
                    types["title_1"] += 1
                    continue
            if ("．" in self.res[i]["text"])and(types["title_2"] > 0): #三级标题
                flag = True
                for j in self.res[i]["text"].split("．")[0]:
                    if not j in num:
                        flag = False
                if flag:
                    self.res[i]["type"] = "title_3"
                    types["title_3"] += 1
                    continue
            if (self.res[i]["text"][0] == "（")and("）" in self.res[i]["text"])and(types["title_1"] > 0): #二、四级标题
                flag_2 = True
                flag_4 = True
                for j in self.res[i]["text"].split("（")[1].split("）")[0]:
                    if not j in num_zh:
                        flag_2 = False
                    if not j in num:
                        flag_4 = False
                if flag_2:
                    self.res[i]["type"] = "title_2"
                    types["title_2"] += 1
                    continue
                if flag_4 and (types["title_3"] > 0):
                    self.res[i]["type"] = "title_4"
                    types["title_4"] += 1
                    continue
            if (self.res[i]["page"] == self.page_num)and(self.res[i]["bbox"][1] > 700): #版记
                self.res[i]["type"] = "note"
                types["note"] += 1
                continue
            if (self.res[i]["page"] == self.page_num)and(types["date"] > 0)and(types["note"] == 0): #联系方式
                self.res[i]["type"] = "contact"
                types["contact"] += 1
                continue
            if (types["title"] > 0)and(types["org"] == 0)and(types["date"] == 0): #正文
                self.res[i]["type"] = "text"
                types["text"] += 1
                continue
            self.res[i]["type"] = "others"
            types["others"] += 1

    def analyze_type(self):
        """xmq
        分析公文类型,通过ai分析pdf第一页内容
        返回: 公文类型标记
        """
        text = self.doc.load_page(0).get_text()
        
        r = askAI(f'''
              你是一个公文pdf内容分析助手,请分析由pymupdf读取的pdf页面内容的第一页，判断公文的类型,优先根据标题后面的关键字判断，若无法判断则根据内容判断。
              类型标记为 1: 函,2: 通知,3: 请示,4: 报告,5: 批复,6: 纪要,7: 通报,8: 决定 ,若为其他或无法判断则为0。
              仅需返回类型标记，无需返回其他内容。         
              页面的文字内容如下：
              {text}
              ''')
        
        if r == -1:
            print("ai连接失败")
            return -1
        else:
            self.type = int(rm_think(r))
            return self.type

    def extract_text(self):
        """xmq
        提取PDF文本内容
        返回: { 
                "公文标题": "",
                "正文内容": "",
                ...
              }
        """
        
        # 过滤掉包含'image'的blocks
        text_pages = []
        for page in self.pages:
            text_page = page
            filtered_blocks = [b for b in text_page['blocks'] if 'image' not in b]
            text_page['blocks'] = filtered_blocks
            # print(text_page)
            text_pages.append(text_page)
        
        r = askAI('''你是一个公文pdf内容分析助手,请分析由pymupdf读取的pdf页面内容，提取文本内容。
              返回格式为  {  
                          "公文标题": "正文黑体标题（非红头文件头），如为多行则需要保留换行标志 \ n",
                          "正文内容": "正文内容,需要包括抬头、附件等所有内容",
                          "落款单位": "文末落款单位(如有)",
                          "落款日期": "落款日期(如有)"
                          "联系人及联系方式":"若公文落款后包含(联系人：xxx ,联系电话：xxxxxxx)则提取出来,否则为空字符串"
                         }
              无需返回其他内容。
              pymupdf读取的字典文本内容如下:\n'''
              + text_pages.__str__()
              )
        
        if r == -1:
            print("AI连接失败")
            return -1
        else:
            # 解析返回结果，返回json
            r = r.strip()
            try:
                r = json.loads(r[7:-3])
                return r
            except json.JSONDecodeError:
                print(f"返回结果json解析失败：\n {r}")
                return -1


if __name__ == "__main__":
    #pdf = PDFParser("../关于召开四川省计算机学会第八次会员代表大会的通知.pdf")
    pdf = PDFParser("../关于进一步明确公司数字空间网络安全责任的通知.pdf")    
    print(pdf.res)
    
    #print(pdf.read_pdf_AI())
    
    # for i in pdf.res:
    #     if i['type'] == 'org' or i['type'] == 'date':
    #         print(i)
            
    # for i in pdf.pic:
    #     if i['type'] == 'stamp':
    #         print(i)
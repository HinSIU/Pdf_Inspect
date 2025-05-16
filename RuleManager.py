from AI import askAI , rm_think
import json 

def has_method(cls, method_name):
    return hasattr(cls, method_name) and callable(getattr(cls, method_name))


def ParseRuleToPrompt(prompt_path:str, id_list:list):
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_dict = json.load(f)
    
    prompt="你是一个公文规范检测辅助专家，请对由pymupdf读取的公文内容格式等进行检查，判断是否符合以下规则。"
    
    for i in id_list:  
        i = str(i)
        rule_name = f'rule_{i}'
        rule_decs = prompt_dict[i]['prompt']
        
        rule_prompt = f'''{rule_name} : {rule_decs}'''
        
        if 'positive' in prompt_dict[i]:
            rule_positive = prompt_dict[i]['positive']
            rule_prompt = rule_prompt + f"\n   正确例子：{rule_positive}"
        if 'negative' in prompt_dict[i]:
            rule_negative = prompt_dict[i]['negative']
            rule_prompt = rule_prompt + f"\n   错误例子：{rule_negative}"
            
        prompt = prompt + f"\n{rule_prompt}"
        
    ret_prompt = '''\n\n检查结果以json格式字符串输出,无需返回其他内容：{rule_XX: (true/false, 检测结果解释，200字以内), ...}'''
    prompt = prompt + ret_prompt

    return prompt

class RuleManager:
    
    def __init__(self,res:list, pic:list, page_num:int , pages:list):
        self.res = res # 文本
        self.pic = pic # 图片
        self.page_num = page_num # 页数
        self.pages = pages
    
    def start(self):
        """xmq
        执行规则检测，
        获取RuleManager类的所有以rule_开头的方法，
        按规则编号顺序执行规则检测，
        返回值为字典，键为规则编号，值为元组或列表（布尔值，描述）
        布尔值为True表示通过，False表示不通过
        
        AI增强检测:
        通过ParseRuleToPrompt读取prompt.json设定的AI检测说明，
        多个规则构造一个prompt调用AI批量检测
        """ 
        
        r = {}
        # 按序号执行固定规则检测
        for i in range(1,200): 
          if hasattr(self, f"rule_{i}") and callable(getattr(self, f"rule_{i}")):
            try :
              tmp_r = {f"rule_{i}":getattr(self, f"rule_{i}")()}
            except Exception as e:
              print(f"执行规则{i}时出错：{e}")
              tmp_r = {f"rule_{i}":(False, '执行规则时出错')}
              
            r.update(tmp_r)



        # AI增强检测示例（输入第一页dict, 检查rule1-6,标题相关规范）
        rule_prompt = ParseRuleToPrompt('prompt.json', [1,2,3,4,5,6])
        input_prompt = f"\n\n 读取的第一页内容如下：{str(self.pages[0])}"
        final_prompt = rule_prompt + input_prompt
 
        print(f"step：通过AI检测规则1-6...",end="")
        AI_r = askAI(final_prompt)
        print(f"完成:\n{AI_r}")
        # 处理返回内容为json
        try:
            AI_r = json.loads(rm_think(AI_r)[7:-3])
            r.update(AI_r)        # 合并检测结果  
        except Exception as e:
            print(f"Error: AI处理出错：{e}")      
        
        return r
    
    def rule_7(self):
        blocks = self.res 
        res = True
        des = ""
        title_text = ""
        
        for i in range(len(blocks)):
            if blocks[i]["type"] == "title":
                title_text += blocks[i]["text"] + "\n"
        title_lines = title_text.strip().split("\n")
        for i in range(len(title_lines)):
            line = title_lines[i]
            l = 0
            for j in line:
                if ord(j) >= 0x100:
                    l += 2
                else:
                    l += 1
            if i == 0:
                l_0 = l
                flag = 0
                continue
            if (l > l_0)and(flag == -1):
                res = False
                des = "标题形状不规则"
            if (l > l_0):
                flag = 1
            if (l < l_0):
                flag = -1
            l_0 = l
        return (res,des)
    
    def rule_10(self):
        blocks = self.res
        res = True
        des = ""
        count = 0
        for i in range(len(blocks)):
            if (blocks[i]["type"] == "org")or(blocks[i]["type"] == "date"):
                count += 1
                if blocks[i]["bbox"][0]+blocks[i]["bbox"][0] < 300:
                    res = False
                    tmp = "发文机关/成文日期不在右侧"
                    if not tmp in des:
                        des += "\n" + tmp
            if (count > 0)and(blocks[i]["type"] == "text"):
                res = False
                tmp = "发文机关/成文日期下方存在正文。"
                if not tmp in des:
                    des += "\n" + tmp
            if (count > 0)and(blocks[i]["type"] == "addons"):
                res = False
                tmp = "发文机关/成文日期下方存在附件说明。"
                if not tmp in des:
                    des += "\n" + tmp
        des = des.strip()
        return (res,des)
    
    def rule_11(self):
        blocks = self.res
        res = True
        des = ""
        note = 0
        for i in range(len(blocks)):
            if blocks[i]["type"] == "note":
                if (note == 0)and(blocks[i-1]["bbox"][1] - blocks[i-1]["bbox"][1] < 40):
                    res = False
                    tmp = "版记与上文未间隔一行"
                    if not tmp in des:
                        des += "\n" + tmp
                note = 1
            if (note == 1)and(blocks[i]["type"] != "note")and(blocks[i]["type"] != "page_num")and(blocks[i]["type"] != "others"):
                res = False
                tmp = "版记后有其他内容"
                if not tmp in des:
                    des += "\n" + tmp
        des = des.strip()
        return (res,des)
    
    def rule_12(self):
        blocks = self.res
        res = True
        des = ""
        for i in range(len(blocks)):
            if (blocks[i]["type"] == "note")and(blocks[i]["page"]%2):
                res = False
                des = "版记不在偶数页"
        return (res,des)
    
    def rule_13(self):
        blocks = self.res
        res = True
        des = ""
        for i in range(len(blocks)):
            if (blocks[i]["type"] == "text")and(blocks[i]["bbox"][3] < 519)and(blocks[i+1]["type"] == "text")and(blocks[i+1]["bbox"][0] < 85):
                res = False
                tmp = "第%d页，“%s”处未两端对齐"%(blocks[i]["page"],blocks[i]["text"][:10])
                des += "\n" + tmp
        des = des.strip()
        return (res,des)

    def rule_36(self):
        """xmq
        检测印章格式规范
        印章需注意骑年压月:
          提取日期和印章，日期中心在（印章边界-日期行高）之内则符合
        输入: res,pic
        """
        date = None 
        stamp = None
        
        # 构造返回
        r = ( False, '未检测' )
        # 读取落款单位、日期
        for i in self.res:
          if i['type'] == 'date':
            date = i
        # 读取印章
        for i in self.pic:
          if i['type'] == 'stamp':
            stamp = i
        
        if stamp and date:
            # 获取日期行高，若日期中心在印章边界-日期行高之内，则符合
            dif = date['bbox'][-1] - date['bbox'][1]
            
            # 计算日期中心
            date_center_x = (date['bbox'][0] + date['bbox'][2]) / 2
            date_center_y = (date['bbox'][1] + date['bbox'][3]) / 2
            
            if  (stamp['bbox'][1] + dif) <= date_center_y <= (stamp['bbox'][3] - dif) \
                and (stamp['bbox'][0] + dif) <= date_center_x <= (stamp['bbox'][2] - dif):
                
                r = (True, '日期中心位于印章边界-日期行高之内')
            else:
                r = (False, '印章未正确骑年压月')
        else:
            r = (False, '缺少印章或日期信息')
        
        return r
        
    def rule_37(self):
        """xmq
        成文日期及印章应居发文机关中心位置
          印章中心x坐标，在发文机关中心x坐标 +- 15 内 且
          印章中心y坐标，在发文机关中心y坐标 -8 +20 内
        检测成文日期应居发文机关中心位置
          日期中心x坐标，与发文机关中心x坐标 +- 8 内 
        输入: res,pic
        """
        stamp = None
        org = None
        date = None
        # 构造返回
        r = (False, '未检测')
        # 读取落款单位、日期
        for i in self.res:
          if i['type'] == 'org':
            org = i
          if i['type'] =='date':
            date = i
        for i in self.pic:
          if i['type'] =='stamp':
            stamp = i
            
        if stamp and org and date:
            stamp_center_x = (stamp['bbox'][0] + stamp['bbox'][2]) / 2
            stamp_center_y = (stamp['bbox'][1] + stamp['bbox'][3]) / 2
            org_center_x = (org['bbox'][0] + org['bbox'][2]) / 2  
            org_center_y = (org['bbox'][1] + org['bbox'][3]) / 2
            date_center_x = (date['bbox'][0] + date['bbox'][2]) / 2

            # print(f"印章中心：({stamp_center_x}, {stamp_center_y})")
            # print(f"发文机关中心：({org_center_x}, {org_center_y})")  
            
            if  (org_center_x - 15) <= stamp_center_x <= (org_center_x + 15) \
                and (org_center_y - 8) <= stamp_center_y <= (org_center_y + 20) \
                and abs(date_center_x - org_center_x) <= 8:
                r  = (True, '成文日期及印章已居发文机关中心位置')
            else:
                r = ( False, '成文日期及印章不在发文机关中心位置')
        else:
            r = (False, '缺少印章、发文机关或日期信息')
                
        return r
    
    def rule_38(self):
        """xmq
        印章不能单独在一页，可适当调整正文行距（22-36磅之间）使得印章页有正文或附件说明内容。
            获取印章所在页数，查找相同页数下是否存在text或addons
        输入: res , pic 
        """
        stamp = None
        # 构造返回
        r = (False, '未检测')
        # 读取印章
        for i in self.pic:
          if i['type'] =='stamp':
            stamp = i
        if stamp:
            # 获取印章所在页数
            stamp_page = stamp['page']
            # 查找相同页数下是否存在type为text或addons
            r = (False, '印章所在页未找到正文或附件')
            for i in self.res:
              if i['page'] == stamp_page and (i['type'] == 'text' or i['type'] == 'addons'):
                if i['page'] == stamp_page:
                    r = ( True, '印章页有正文或附件说明内容')
                    break 
        else:
            r = ( False, '缺少印章信息')
        
        return r  

    def rule_40(self):
        """xmq
        标点符号 ：，应为中文格式下标点。
          遍历所有text，检查标点符号是否存在应为标点符号:,
        输入: res
        """
        r = (False, '未检测')
        en_chars = [',', ":"]
        for i in self.res:
            if i['type'] == 'text':
                text = i['text']
                if any(char in text for char in en_chars):
                    r = ( False, f'标点符号包含非中文格式下标点  {text}')
        
        r = ( True, '标点符号均为中文格式下标点')
        
        return r

    def rule_43(self):
      """xmq
      检查是否存在空页
        遍历页数，若页数不存在text或addons则为空页
      输入: res , page_num
      """
      r = ( False, '未检测')
      
      empty_page = []
      # 检查是否存在空页
      for i in range(1,1+self.page_num):
          if not any(item['page'] == i and (item['type'] == 'text' or item['type'] == 'addons') for item in self.res):
              empty_page.append(i)
      
      if len(empty_page) == 0:
        r = ( True, '不存在空页')
      else:
        r = ( False, f'存在空页 {empty_page}')
        
      return r










## 以下是AI检测

    def check_title_rules_AI(self , pdf_title_text:str , type:str):
        """标题规范检测——AI
        输入: 标题文本str, 公文类型str
        """
        
        r = askAI('''
              请根据提供的公文标题文本和公文类型，判断标题是否符合规范。
              标题规则1：回行不应断开词意，如AB为一个词，则不能存在行换导致 A换行B 的情况。
                正确例子：
                1. 标题1：“关于开展网络安全培训的\n通知”
                2. 标题2：“关于开展第八次会员代表\n大会的通知”
                错误例子：
                1. 标题1：“关于开展网\n络安全培训的通知”
                2. 标题2：“关于开展第八次会员代\n表大会的通知”
              标题规则2：“的”“等”等介词不能作为标题开头及换行开头。
              标题规则3：标题排版断句时，连词需要紧密连接后面内容，所以“暨”“和”“及”等连词应排列在行首。
              标题规则4：标题中的计量单位应使用中文。
              标题规则5：标题应由发文单位名称（全称或规范化简称）、事由和文种组成。
              标题规则6：若公文为会议纪要，则标题格式为：“会议名称”+纪要。
              标题规则7：标题多行排列时不能存在上下行长、中间短的漏斗形。
              根据以上规则检测公文标题是否符合规范。
              只返回检测结果json
              {
                "标题规则1":[true/false,'检测结果解释，200字以内'],
                "标题规则2":[true/false.'检测结果解释，200字以内'],
                ...
              }
              无需返回其他内容。''' + 
              f'公文类型为：{type} \n ' + 
              f'公文标题文本如下：\n{pdf_title_text}')
        
        r = rm_think(r).strip()
        return r #json.loads(r[7:-3])
      
    def check_note_rules_AI(self , page_dic , page_num , type):
        """落款日期及版记排版检测—AI
        输入: pymupdf读取的最后一页字典dict, 总页数int, 公文类型str
        """
        r = askAI('''
              请根据提供的pymupdf读取最后一页内容，判断是否符合以下规范。
              
              落款规则：落款的发文机关、落款日期应位于正文/附件说明右下方。
              版记规则：版记应在页面底部沉底，与成文日期至少隔一行。
              页数规则：除类型为函外的公文，总页数一定是偶数页。

              只需返回检测结果json
              {
                "落款规则":[true/false,'检测结果解释，200字以内'],
                "版记规则":[true/false,'检测结果解释，200字以内'],
                "页数规则":[true/false,'检测结果解释，200字以内'],
                ...
              }
              无需返回其他内容。''' + 
              f'文档总页数为：{page_num} \n'+
              f'文档最后一页内容如下：\n{page_dic.__str__()}'
              )
        
        r = rm_think(r).strip()
        return r # json.loads(r[7:-3])


if __name__ == "__main__":
    ParseRule_AI('prompt.json',[1,2,3,4,5,6])
from PDFParser import PDFParser
from RuleManager import RuleManager
import sys

doctype = ['其他','函','通知','请示','报告','批复','纪要','通报','决定']

#pdf = PDFParser("../关于召开四川省计算机学会第八次会员代表大会的通知.pdf")
pdf = PDFParser(sys.argv[1])    

# 初始化规则管理器 ， 规则校验都写在RuleManager中
# 通过实例化RuleManager，调用函数检查
# 输入的参数自行通过PDFParser获取，若没有需要自行编写函数提取
# 返回格式为json：
            #   {
            #     "规则1":[true/false,'检测结果解释，200字以内'],
            #     "规则2":[true/false.'检测结果解释，200字以内'],
            #     ...
            #   }
RM = RuleManager(pdf.res,pdf.pic,pdf.page_num,pdf.pages) # 初始化时已经调用了AI进行识别部分数据，若不需要请到PDFParser中注释掉对应代码

r = RM.start() # 调用规则检查函数，传入参数(自行编写或通过PDFParser获取..)

for key in r: # 打印检测结果
    if not r[key][0]:
        print(f"不通过：{key} -- {r[key][1]}" )
    else:
        print(f"通过：{key} -- {r[key][1]}" )





# # 检测标题规范
# print("step：通过AI检测标题规范...",end="")
# title_check_result = RM.check_title_rules_AI(pdf.text["公文标题"], doctype[pdf.type])
# print(f"完成:\n{title_check_result}")


# # 检测落款、版记排版
# print("step：通过AI检测落款、版记排版规范...",end="")
# note_check_result = RM.check_note_rules_AI(pdf.pages[-1] , len(pdf.pages) , doctype[pdf.type])
# print(f"完成:\n{note_check_result}")



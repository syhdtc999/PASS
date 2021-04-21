import pygame
from pygame.color import THECOLORS
from random import randint
import random
import threading

#地图大小
MAPSIZE=(9,9)
#障碍物总数
BLOCK_NUM=0
#三种不同范围的权重
WEIGHT1 = 0.5
WEIGHT2 = 0.4
WEIGHT3 = 0.1
#单元格宽度/高度/边界宽度
CELL_WIDTH=25
CELL_HEIGHT = 25
BORDER_WIDTH=1
#五种不同威胁程度的障碍物颜色RGB值
COLOR_TH1 = [209, 211, 224]
COLOR_TH2= [188, 194, 215]
COLOR_TH3= [136, 149, 177]
COLOR_TH4= [84, 108, 140]
COLOR_TH5= [25, 69, 104]
#无人机数量
UAV_NUM=2
#是否冲突标志位
CONFLICT_FLAG=0
#所有无人机期望的模块中心点列表
DECISIONS=[]

#生成障碍物的函数，返回障碍物威胁等级的字典
def gen_blocks():
    realblocklist=[]
    extra_blocklist=[]
    blocklistdic={}

    #地图的最外边一圈都是实打实的障碍
    for i in range(MAPSIZE[1]+2):
        realblocklist.append((0,i))
    for i in range(MAPSIZE[0]+2):
        realblocklist.append((i,0))
    for i in range(MAPSIZE[1]+2):
        realblocklist.append((MAPSIZE[0]+1,i))
    for i in range(MAPSIZE[0]+2):
        realblocklist.append((i,MAPSIZE[1]+1))
    #集合去重（四个角落被算了两次）
    realblocklist=list(set(realblocklist))

    #生成四角三角形区域的实打实的障碍
    #左上角
    for i in range(MAPSIZE[0]//3):
        for j in range(MAPSIZE[1]//3 - i):
            realblocklist.append((i+1, j+1))
    #右上角
    for i in range(MAPSIZE[0]//3):
        for j in range(MAPSIZE[1]//3-i):
            realblocklist.append((MAPSIZE[0]-1-i+1,j+1))
    #左下角
    for i in range(MAPSIZE[0]//3):
        for j in range(MAPSIZE[1]//3-i):
            realblocklist.append((i+1,MAPSIZE[1]-1-j+1))
    #右下角
    for i in range(MAPSIZE[0]//3):
        for j in range(MAPSIZE[1]//3-i):
            realblocklist.append((MAPSIZE[0]-1-i+1,MAPSIZE[1]-1-j+1))

    #指定这些实打实的障碍的威胁等级是5
    for (x,y) in realblocklist:
        blocklistdic[(x,y)]=5

    realblocklist.append((5,3))
    realblocklist.append((6,2))
    realblocklist.append((7,3))
    realblocklist.append((8,4))
    realblocklist.append((7,5))
    realblocklist.append((6,6))
    realblocklist.append((5,5))
    realblocklist.append((4,4))
    # # realblocklist.append()
    # realblocklist.append((9,5))
    # realblocklist.append((7,4))

    #指定这些实打实的障碍的威胁等级是5
    for (x,y) in realblocklist:
        blocklistdic[(x,y)]=5

    i=0
    #在此之后，在障碍物列表里面额外再加BLOCK_NUM个障碍
    while(i < BLOCK_NUM):
        block = (randint(1, MAPSIZE[0]), randint(1,MAPSIZE[1]))
        if block not in extra_blocklist and block not in realblocklist:
            extra_blocklist.append(block)
            i+=1

    #随机指定后加的BLOCK_NUM个障碍的威胁等级
    for (x,y) in extra_blocklist:
        th=randint(1,5)
        blocklistdic[(x,y)]=th

    return blocklistdic

#该函数把障碍物威胁等级的字典转换为对应威胁程度的字典
def  transform_dic_to_thdic(blocklistdic):
    blocklistthdic={}
    for item in blocklistdic:
        if blocklistdic[item]==1:
            blocklistthdic[item]=0.2
        elif blocklistdic[item]==2:
            blocklistthdic[item]=0.4
        elif blocklistdic[item]==3:
            blocklistthdic[item]=0.6
        elif blocklistdic[item]==4:
            blocklistthdic[item]=0.8
        elif blocklistdic[item]==5:
            blocklistthdic[item]=1
    return blocklistthdic

#该函数把逻辑坐标列表转换为像素坐标列表
def transform_lst(lst):
    result_pix_lst=[]
    for (x,y) in lst:
        result_pix_lst.append((x*CELL_WIDTH,y*CELL_HEIGHT))
    return result_pix_lst

#绘制航迹用的函数
def transform_lst_point(lst):
    result_pix_lst=[]
    for (x,y) in lst:
        result_pix_lst.append((x*CELL_WIDTH+0.5*CELL_WIDTH,y*CELL_HEIGHT+0.5*CELL_HEIGHT))
    return result_pix_lst

#地图类
class Map(object):
    def __init__(self, map_pixsize):
        self.map_pixsize = map_pixsize
    def generate_cell(self):
        '''
        定义一个生成器，用来生成地图中的所有节点坐标
        :param cell_width: 节点宽度
        :param cell_height: 节点长度
        :return: 返回地图中的节点
        '''
        x_cell = -CELL_WIDTH
        for num_x in range(self.map_pixsize[0] // CELL_WIDTH):
            y_cell = -CELL_HEIGHT
            x_cell += CELL_WIDTH
            for num_y in range(self.map_pixsize[1] // CELL_HEIGHT):
                y_cell += CELL_HEIGHT
                yield (x_cell, y_cell)

class UAV(object):
    #无人机的初始化程序
    def __init__(self,ID,pos,test_mode=False):
        #无人机编号
        self.ID=ID
        #无人机所在位置坐标
        self.pos = pos
        #无人机图片
        self.pic_path='uav'+str(ID)+'.png'
        #无人机的飞行方向，默认向上
        self.orientation=(0,-1)
        #无人机飞行方向与邻居模块位置关系的字典
        self.orientation_dic={1:(0,-1),4:(-1,0),3:(0,1),2:(1,0)}
        #无人机所在模块中心点坐标(默认左上)
        self.module_center=(pos[0]-0.5,pos[1]-0.5)
        self.module_center_confirm()
        #无人机邻居模块的单元格坐标列表，此处隐藏更新了属性neighbour_module_unit_dic
        self.neibour_unit_pos=self.get_unit_from_neighbour_module()
        #默认工作模式，0为睡眠模式
        self.mode=1
        #无人机剩余电量
        self.battery=999999
        #无人机的飞行总路程
        self.distance=0
        #无人机所处的步数
        self.step=0
        #无人机的航拍影像
        self.photo=self.take_pohto()
        #无人机的黑匣子
        current_state=(self.pos,self.orientation,self.module_center,self.photo,
                       self.neighbour_module_unit_dic,self.mode,self.battery,self.distance,self.step)
        self.black_box=[current_state]
        #无人机的历史飞行状态记录器，与黑匣子的区别仅在于,它是可以修改的，在决定退回时会用到
        self.history_states=self.black_box.copy()
        # if ID==1:
        #     color='橙'
        # elif ID==2:
        #     color='黄'
        # elif ID==3:
        #     color='绿'
        # elif ID==4:
        #     color='棕'
        self.test_mode=test_mode
        print('无人机' + str(self.ID) + '初始化成功! 初始位置' + str(self.pos))
        assert self.step==0
        print('step：'+str(self.step)+' 航拍结果:'+str(self.photo))

    #记录当前所在模块的障碍物分布情况
    def take_pohto(self):
        l_u=(int(self.module_center[0]-0.5),int(self.module_center[1]-0.5))
        r_u=(int(self.module_center[0]+0.5),int(self.module_center[1]-0.5))
        l_l=(int(self.module_center[0]-0.5),int(self.module_center[1]+0.5))
        r_l=(int(self.module_center[0]+0.5),int(self.module_center[1]+0.5))
        photo={l_u:BLOCKLISTDIC.get(l_u,0),r_u:BLOCKLISTDIC.get(r_u,0),l_l:BLOCKLISTDIC.get(l_l,0),r_l:BLOCKLISTDIC.get(r_l,0)}
        return photo

    #确认（有可能会修改）无人机所处的模块中心(仅供初始化时使用)
    def module_center_confirm(self):
        if MAPSIZE[0]-0.5>=self.module_center[0]>=0.5+1 and 1+0.5<=self.module_center[1]<=MAPSIZE[1]-0.5:
            pass
        else:
            module_center=(self.module_center[0],self.module_center[1])
            possible_offset=[(1,0),(1,1),(0,1)]
            for i in range(3):
                module_center=(module_center[0]+possible_offset[i][0],module_center[1]+possible_offset[i][1])
                if MAPSIZE[0]-0.5>=module_center[0]>=0.5+1 and 1.5<=module_center[1]<=MAPSIZE[1]-0.5:
                    self.module_center=module_center
                    break
                else:
                    module_center=(module_center[0]-possible_offset[i][0],module_center[1]-possible_offset[i][1])
                    continue

    #获取邻居模块的单元格信息
    def get_unit_from_neighbour_module(self):
        #可能的邻居模块中心点坐标
        neighbour_module_center_list=[]
        #每架无人机的侦察范围
        offsets=[(0,-2),(2,0),(0,2),(-2,0)]
        for i in range(4):
            neighbour_module_center_list.append((self.module_center[0]+offsets[i][0],self.module_center[1]+offsets[i][1]))
        # print(neighbour_module_center_list)
        self.neighbour_module_unit_dic={}
        j=0
        #真正邻居模块所含单元格坐标列表
        neighbour_module_unit_list=[]
        flag=0
        temp_list=[]
        for (x,y) in neighbour_module_center_list:
            if 1<=(x-0.5)<=MAPSIZE[0] and 1<=(y-0.5)<=MAPSIZE[1]:
                neighbour_module_unit_list.append((int(x-0.5),int(y-0.5)))
                temp_list.append((int(x-0.5),int(y-0.5)))
                flag=1
            if 1<=(x+0.5)<=MAPSIZE[0] and 1<=(y-0.5)<=MAPSIZE[1]:
                neighbour_module_unit_list.append((int(x+0.5),int(y-0.5)))
                temp_list.append((int(x+0.5),int(y-0.5)))
                flag=1
            if 1<=(x+0.5)<=MAPSIZE[0] and 1<=(y+0.5)<=MAPSIZE[1]:
                neighbour_module_unit_list.append((int(x+0.5),int(y+0.5)))
                temp_list.append((int(x+0.5),int(y+0.5)))
                flag=1
            if 1<=(x-0.5)<=MAPSIZE[0]  and 1<=(y+0.5)<= MAPSIZE[1]:
                neighbour_module_unit_list.append((int(x-0.5), int(y + 0.5)))
                temp_list.append((int(x-0.5),int(y+0.5)))
                flag=1
            j+=1
            if flag==1:
                self.neighbour_module_unit_dic[j]=temp_list
            else:
                self.neighbour_module_unit_dic[j]=[]
            flag=0
            temp_list=[]
        return neighbour_module_unit_list

    #计算新的模块中心点坐标（在平时飞行时使用）
    def calc_module_center(self,pos_new,orientation_new):
        for i in range(1,5):
            #必然存在一个i
            if pos_new in self.neighbour_module_unit_dic[i]:
                if len(self.neighbour_module_unit_dic[i])==4:
                    sum_x=0
                    sum_y=0
                    for x,y in self.neighbour_module_unit_dic[i]:
                        sum_x+=x
                        sum_y+=y
                    new_module_center=(sum_x/4,sum_y/4)
                else:
                    #新模块只有一半
                    new_module_center=(self.module_center[0]+2*orientation_new[0],self.module_center[1]+2*orientation_new[1])
        return new_module_center

    #这个函数返回各个邻居模块对应的cost值
    #对于所含单元格都为障碍物的模块，cost=1/2.1；对于不可达的模块，cost=0
    def auction(self):
        module_cost_dic={}
        (x,y)=self.module_center
        l_u = (int(x - 0.5), int(y - 0.5))
        r_u = (int(x + 0.5), int(y - 0.5))
        l_l = (int(x - 0.5), int(y + 0.5))
        r_l = (int(x + 0.5), int(y + 0.5))
        #自身模块所包含的合法单元格
        possible_self_module_units=[l_u,r_u,l_l,r_l]
        self_module_units=[]
        for unit in possible_self_module_units:
            if 0<=unit[0]<=MAPSIZE[0]+1 and 0<=unit[1]<=MAPSIZE[1]+1:
                self_module_units.append(unit)

        cost1=0
        cost2=0
        cost3=0
        cost4=0
        #可能的大权值单元格坐标集合
        possible_near_neighbour={(x-0.5,y-1.5),(x+0.5,y-1.5),(x+1.5,y-0.5),(x+1.5,y+0.5),(x-0.5,y+1.5),(x+0.5,y+1.5),(x-1.5,y-0.5),(x-1.5,y+0.5)}
        #模块一包含的合法单元格
        l_u_u=(l_u[0],l_u[1]-1)
        l_u_u_u=(l_u[0],l_u[1]-2)
        r_u_u=(r_u[0],r_u[1]-1)
        r_u_u_u=(r_u[0],r_u[1]-2)
        possible_one_module_units=[l_u_u,l_u_u_u,r_u_u,r_u_u_u]
        one_module_units=[]
        for unit in possible_one_module_units:
            if 0<=unit[0]<=MAPSIZE[0]+1 and 0<=unit[1]<=MAPSIZE[1]+1:
                one_module_units.append(unit)
        possible_weight1_units = [(self.pos[0], self.pos[1] - 1), (self.pos[0] - 1, self.pos[1] - 1),
                                  (self.pos[0] + 1, self.pos[1] - 1)]
        for unit in possible_weight1_units:
            if unit in self_module_units:
                cost1+=WEIGHT1*BLOCKLISTTHDIC.get(unit,0)
        if one_module_units==[]:
            cost1=0
        else:
            for unit in one_module_units:
                if unit in possible_near_neighbour:
                    cost1+=WEIGHT2*BLOCKLISTTHDIC.get(unit,0)
                else:
                    cost1+=WEIGHT3*BLOCKLISTTHDIC.get(unit,0)
        cost1=1/(0.1+cost1)

        #模块二包含的合法单元格
        r_u_u=(r_u[0]+1,r_u[1])
        r_u_u_u=(r_u[0]+2,r_u[1])
        r_l_l=(r_l[0]+1,r_l[1])
        r_l_l_l=(r_l[0]+2,r_l[1])
        possible_two_module_units=[r_u_u,r_u_u_u,r_l_l,r_l_l_l]
        two_module_units=[]
        for unit in possible_two_module_units:
            if 0<=unit[0]<=MAPSIZE[0]+1 and 0<=unit[1]<=MAPSIZE[1]+1:
                two_module_units.append(unit)
        possible_weight1_units = [(self.pos[0] + 1, self.pos[1] - 1), (self.pos[0] + 1, self.pos[1]),
                                  (self.pos[0] + 1, self.pos[1] + 1)]
        for unit in possible_weight1_units:
            if unit in self_module_units:
                cost2+=WEIGHT1*BLOCKLISTTHDIC.get(unit,0)
        if two_module_units==[]:
            cost2=0
        else:
            for unit in two_module_units:
                if unit in possible_near_neighbour:
                    cost2+=WEIGHT2*BLOCKLISTTHDIC.get(unit,0)
                else:
                    cost2+=WEIGHT3*BLOCKLISTTHDIC.get(unit,0)
        cost2=1/(0.1+cost2)

        # 模块三包含的合法单元格
        l_l_l= (l_l[0],l_l[1]+1)
        l_l_l_l= (l_l[0],l_l[1]+2)
        r_l_l = (r_l[0], r_l[1]+1)
        r_l_l_l = (r_l[0], r_l[1]+2)
        possible_three_module_units = [l_l_l, l_l_l_l, r_l_l, r_l_l_l]
        three_module_units = []
        for unit in possible_three_module_units:
            if 0 <= unit[0] <= MAPSIZE[0]+1  and 0 <= unit[1] <= MAPSIZE[1]+1 :
                three_module_units.append(unit)
        possible_weight1_units = [(self.pos[0], self.pos[1] + 1), (self.pos[0] - 1, self.pos[1] + 1),
                                  (self.pos[0] + 1, self.pos[1] + 1)]
        for unit in possible_weight1_units:
            if unit in self_module_units:
                cost3+=WEIGHT1*BLOCKLISTTHDIC.get(unit,0)
        if three_module_units==[]:
            cost3=0
        else:
            for unit in three_module_units:
                if unit in possible_near_neighbour:
                    cost3 += WEIGHT2 * BLOCKLISTTHDIC.get(unit, 0)
                else:
                    cost3 += WEIGHT3 * BLOCKLISTTHDIC.get(unit, 0)
        cost3=1/(0.1+cost3)

        # 模块四包含的合法单元格
        l_u_u= (l_u[0]-1,l_u[1])
        l_u_u_u= (l_u[0]-2,l_u[1])
        l_l_l = (l_l[0]-1, l_l[1])
        l_l_l_l = (l_l[0]-2, l_l[1])
        possible_four_module_units = [l_u_u, l_u_u_u, l_l_l, l_l_l_l]
        four_module_units = []
        for unit in possible_four_module_units:
            if 0 <= unit[0] <= MAPSIZE[0]+1 and 0 <= unit[1] <= MAPSIZE[1]+1:
                four_module_units.append(unit)
        possible_weight1_units = [(self.pos[0] - 1, self.pos[1] + 1), (self.pos[0] - 1, self.pos[1]),
                                  (self.pos[0] - 1, self.pos[1] - 1)]
        for unit in possible_weight1_units:
            if unit in self_module_units:
                cost4+=WEIGHT1*BLOCKLISTTHDIC.get(unit,0)
        if four_module_units==[]:
            cost4=0
        else:
            for unit in four_module_units:
                if unit in possible_near_neighbour:
                    cost4 += WEIGHT2 * BLOCKLISTTHDIC.get(unit, 0)
                else:
                    cost4 += WEIGHT3 * BLOCKLISTTHDIC.get(unit, 0)
        cost4=1/(0.1+cost4)
        module_cost_dic={1:cost1,2:cost2,3:cost3,4:cost4}
        # #可能的大权值单元格坐标集合
        # possible_near_neighbour={(x-0.5,y-1.5),(x+0.5,y-1.5),(x+1.5,y-0.5),(x+1.5,y+0.5),(x-0.5,y+1.5),(x+0.5,y+1.5),(x-1.5,y-0.5),(x-1.5,y+0.5)}
        # # 可能的小权值单元格坐标集合
        # # possible_far_neighbour={(x-0.5,y-2.5),(x+0.5,y-2.5),(x+2.5,y-0.5),(x+2.5,y+0.5),(x-0.5,y+2.5),(x+0.5,y+2.5),(x-2.5,y-0.5),(x-2.5,y+0.5)}
        # l_u = (int(x - 0.5), int(y - 0.5))
        # r_u = (int(x + 0.5), int(y - 0.5))
        # l_l = (int(x - 0.5), int(y + 0.5))
        # r_l = (int(x + 0.5), int(y + 0.5))
        # possible_self_module_units=[l_u,r_u,l_l,r_l]
        # #无人机自身所在模块中真正包含的单元格列表
        # self_module_units=[]
        # for unit in possible_self_module_units:
        #     if MAPSIZE[0]>=unit[0]>=1 and 1<=unit[1]<=MAPSIZE[1]:
        #         self_module_units.append(unit)
        # for i in range(1,5):
        #     cost = 0
        #     if i==1:
        #         possible_weight1_units=[(self.pos[0],self.pos[1]-1),(self.pos[0]-1,self.pos[1]-1),(self.pos[0]+1,self.pos[1]-1)]
        #     elif i==2:
        #         possible_weight1_units=[(self.pos[0]+1,self.pos[1]-1),(self.pos[0]+1,self.pos[1]),(self.pos[0]+1,self.pos[1]+1)]
        #     elif i==3:
        #         possible_weight1_units=[(self.pos[0],self.pos[1]+1),(self.pos[0]-1,self.pos[1]+1),(self.pos[0]+1,self.pos[1]+1)]
        #     elif i==4:
        #         possible_weight1_units=[(self.pos[0]-1,self.pos[1]+1),(self.pos[0]-1,self.pos[1]),(self.pos[0]-1,self.pos[1]-1)]
        #     for unit in possible_weight1_units:
        #         if unit in self_module_units:
        #             print("i=''",i,",unit=",unit)
        #             cost+=BLOCKLISTTHDIC.get(unit,0)*WEIGHT1
        #     if self.neighbour_module_unit_dic[i]!=[]:
        #         for (m,n) in self.neighbour_module_unit_dic[i]:
        #             if (m,n) in possible_near_neighbour:
        #                 cost+=WEIGHT2*BLOCKLISTTHDIC.get((m,n),0)
        #             else:
        #                 cost+=WEIGHT3*BLOCKLISTTHDIC.get((m,n),0)
        #         cost=1/(0.1+cost)
        #         module_cost_dic[i]=cost
        #     else:
        #         module_cost_dic[i]=0


        return module_cost_dic

    # 返回值：直走可以飞几格
    # 已知了方向，再决定飞几格，检查三件事：
    # 1.远近目标点是否跑出地图边界
    # 2.远近目标点是否是障碍，最远的目标点是否位于邻居模块中
    # 3.近目标点以后是否位于邻居模块中
    def straight_num_can_fly(self, orientation):
        destination1 = (self.pos[0] + orientation[0], self.pos[1] + orientation[1])
        destination2 = (self.pos[0] + 2 * orientation[0], self.pos[1] + 2 * orientation[1])
        destination3 = (self.pos[0]+3*orientation[0],self.pos[1]+3*orientation[1])
        #首先看最远的目标点是否超出了地图的边界
        if 1<=destination3[0]<=MAPSIZE[0] and 1<=destination3[1]<=MAPSIZE[1]:
          #如果最远的目标点没有超出地图的边界，可以推出近的两个目标一定没有超越地图的边界
            #如果最远的目标点不是障碍的话
            if (destination3 not in BLOCKLISTTHDIC or BLOCKLISTTHDIC[destination3]!=1):
                #如果最远的目标点也在邻居模块中
                if destination3 in self.neibour_unit_pos:
                    #如果两个次远目标点也不是障碍物的话，那就可以飞三格
                    if ((destination1 not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[destination1] != 1) and (
                            (destination2 not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[destination2] != 1):
                        return 3
                    #远的是障碍，近的不是障碍
                    elif (destination2 in BLOCKLISTTHDIC) and (destination1 not in BLOCKLISTTHDIC or BLOCKLISTTHDIC[destination1]!=1):
                        #再看近的那个是否跑出自己的模块，跑的出去飞一格
                        if destination1 in self.neibour_unit_pos:
                            return 1
                        #跑不出的话飞不了
                        else:
                            return 0
                    #近的那个是障碍物的情形，直接飞不了
                    else:
                        return 0
                #如果最远目标点不在邻居模块中，三格飞不了，判断是否能飞两格
                else:
                    # 然后再看远的和近的目标点是否是威胁程度为1的障碍物
                    if ((destination1 not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[destination1] != 1) and (
                            (destination2 not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[destination2] != 1):
                        return 2
                    # 远的目标点是障碍但是近的目标点不是障碍的情形
                    elif destination1 not in BLOCKLISTTHDIC or BLOCKLISTTHDIC[destination1] != 1:
                        # 这说明近的目标点根本没有跑出当前所处的模块，这种情况飞不了
                        if destination1 not in self.neibour_unit_pos:
                            return 0
                        # 近的目标点在自己所处的模块之外，飞一格
                        else:
                            return 1
                    # 近的目标点是障碍物，直接飞不了
                    else:
                        return 0

        # 看远的目标点是否超越了地图的边界
        if 1 <= destination2[0] <= MAPSIZE[0]  and 1 <= destination2[1] <= MAPSIZE[1] :
            # 如果远的目标点没超出地图边界，那么近的一定不会超出地图边界
            # 然后再看远的和近的目标点是否是威胁程度为1的障碍物
            if ((destination1 not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[destination1] != 1) and (
                    (destination2 not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[destination2] != 1):
                return 2
            # 远的目标点是障碍但是近的目标点不是障碍的情形
            elif destination1 not in BLOCKLISTTHDIC or BLOCKLISTTHDIC[destination1] != 1:
                # 这说明近的目标点根本没有跑出当前所处的模块，这种情况飞不了
                if destination1 not in self.neibour_unit_pos:
                    return 0
                # 近的目标点在自己所处的模块之外，飞一格
                else:
                    return 1
            # 近的目标点是障碍物，直接飞不了
            else:
                return 0

        # 近的的目标点没有超越了地图的边界，远的目标点超越了地图的边界
        elif 1 <= destination1[0] <= MAPSIZE[0] and 1 <= destination1[1] <= MAPSIZE[1] and (not (1 <= destination2[0] <= MAPSIZE[0] and 1 <= destination2[1] <= MAPSIZE[1] )):
            # 近的目标点不是障碍物
            if (destination1 not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[destination1] != 1:
                # 然后再看目标格子是否位于邻居模块中
                if destination1 not in self.neibour_unit_pos:
                    return 0
                # 目标格子跑出了自身所在的单元格，允许飞一格
                else:
                    return 1
            else:
                return 0

        # 远的和近的目标点都跑出了地图的边界，那一格也飞不了
        else:
            return 0

    def count_self_module_units_num(self):
        l_u=(int(self.module_center[0]-0.5),int(self.module_center[1]-0.5))
        r_u=(int(self.module_center[0]+0.5),int(self.module_center[1]-0.5))
        l_l=(int(self.module_center[0]-0.5),int(self.module_center[1]+0.5))
        r_l=(int(self.module_center[0]+0.5),int(self.module_center[1]+0.5))
        possible_self_module_units_num=[l_u,r_u,l_l,r_l]
        count=0
        for unit in possible_self_module_units_num:
            if MAPSIZE[0]>=unit[0]>=1 and 1<=unit[1]<=MAPSIZE[1]:
                count+=1
        return count

    # 返回值：转弯可以飞几格和目标单元格坐标，只在直走只能飞0格的时候触发
    def turn_num_can_fly(self,orientation):
        #case1：自身模块含有的障碍直接挡在前面
        inspect_unit=(self.pos[0]+orientation[0],self.pos[1]+orientation[1])
        #如果考察的单元格位于自身的模块中并且它是障碍的话，会导致只能直飞0格的情形出现
        if inspect_unit in self.take_pohto() and not (inspect_unit not in BLOCKLISTTHDIC or BLOCKLISTTHDIC[inspect_unit]!=1):
            #调出除飞机自身位置和考察单元格以外的剩余两个单元格，形成一个列表
            rest_units=[]
            for unit in self.take_pohto():
                if unit!=self.pos and unit!=inspect_unit:
                    rest_units.append(unit)
            obstacle_flag=0
            #剩余的两个单元格但凡有一个是障碍，直接飞不了（包含了两种情形）
            for unit in rest_units:
                if not (unit not in BLOCKLISTTHDIC or BLOCKLISTTHDIC[unit]!=1):
                    obstacle_flag=1
            if obstacle_flag==1:
                return (0,None)
            #如果剩余的两个单元格都不是障碍，那么再考查目标模块的单元格，即欧式距离的平方为5的单元格，看它是不是障碍物
            else:
                # 确定当前正在考察的目标模块
                orientation_dic_reverse = {(0, -1): 1, (-1, 0): 4, (0, 1): 3, (1, 0): 2}
                # 调出目标模块所含的单元格坐标列表
                units_list = self.neighbour_module_unit_dic[orientation_dic_reverse[orientation]]
                # 建立欧式距离字典
                distance_dic = {}
                for unit in units_list:
                    distance_dic[unit] = (self.pos[0] - unit[0]) ** 2 + (self.pos[1] - unit[1]) ** 2
                for unit in distance_dic:
                    if distance_dic[unit]==5:
                        target_unit=unit
                        break
                if distance_dic!={}:
                    #如果它不是障碍物的话
                    if (target_unit not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[target_unit]!=1:
                        return (3,target_unit)
                    else:
                        return (0,None)
                else:
                    return (0,None)
        #case2、3
        elif not( ((self.pos[0]+orientation[0],self.pos[1]+orientation[1] )not in BLOCKLISTTHDIC or BLOCKLISTTHDIC[(self.pos[0]+orientation[0],self.pos[1]+orientation[1]) ]!=1) and (self.pos[0]+orientation[0],self.pos[1]+orientation[1]) in self.neibour_unit_pos) or (not ((self.pos[0]+2*orientation[0],self.pos[1]+2*orientation[1]) not in BLOCKLISTTHDIC or BLOCKLISTTHDIC[(self.pos[0]+2*orientation[0],self.pos[1]+2*orientation[1]) ]!=1) and (self.pos[0]+2*orientation[0],self.pos[1]+2*orientation[1]) in self.neibour_unit_pos):
            #确定当前正在考察的目标模块
            orientation_dic_reverse={(0,-1):1,(-1,0):4,(0,1):3,(1,0):2}
            #调出目标模块所含的单元格坐标列表
            units_list=self.neighbour_module_unit_dic[orientation_dic_reverse[orientation]]
            self_units_num=self.count_self_module_units_num()
            if len(units_list)==2 and self_units_num==2:
                return (0,None)
            #建立欧式距离字典
            distance_dic={}
            for unit in units_list:
                distance_dic[unit]=(self.pos[0]-unit[0])**2+(self.pos[1]-unit[1])**2
            #按照欧式距离的大小升序排序
            distance_list=list(distance_dic.items())
            distance_list.sort(key=lambda x:x[1])
            if distance_list==[]:
                return (0,None)
            assert BLOCKLISTTHDIC[distance_list[0][0]]==1
            #如果第二名不是障碍，接下来还要判断所在模块障碍物情况，最后再决定飞几格
            if (distance_list[1][0] not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[distance_list[1][0]]!=1:
                if distance_list[1][1]==2:
                    #计算位移差，一定是类似于(-1,1),(1,-1)这样的
                    displacement=(distance_list[1][0][0]-self.pos[0],distance_list[1][0][1]-self.pos[1])
                    #得出垂直于当前方向的位移差，一定是类似于(0,-1),(0,1)这样的
                    vertical_displacement=(displacement[0]-orientation[0],displacement[1]-orientation[1])
                    #计算考察的单元格坐标，如果它不是障碍的话，就可以飞两格，不然飞不了
                    result_unit=(self.pos[0]+vertical_displacement[0],self.pos[1]+vertical_displacement[1])
                    if (result_unit not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[result_unit]!=1:
                        return (2,distance_list[1][0])
                    else:
                        return (0,None)
                #这种情形可以推出当前所在模块一定有四个单元格,给它们建立一个列表
                elif distance_list[1][1]==5:
                    units_in_current_module= [(int(self.module_center[0]-0.5),int(self.module_center[1]-0.5)),
            (int(self.module_center[0]+0.5),int(self.module_center[1]-0.5)),
            (int(self.module_center[0]-0.5),int(self.module_center[1]+0.5)),
            (int(self.module_center[0]+0.5),int(self.module_center[1]+0.5))]
                    #将这个列表按照与当前飞机所在位置的欧式距离进行升序排序
                    units_in_current_module.sort(key=lambda x:(x[0]-self.pos[0])**2+(x[1]-self.pos[1])**2)
                    #如果离飞机最远的那个单元格不是障碍物的话，考察距离次之的两个单元格
                    if (units_in_current_module[-1] not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[units_in_current_module[-1]]!=1:
                        #距离次之的两个单元格中只要有一个不是障碍物，那它就可以飞三格
                        second_far_list=[units_in_current_module[-2],units_in_current_module[-3]]
                        if (second_far_list[0] not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[second_far_list[0]]!=1 or ((second_far_list[1] not in BLOCKLISTTHDIC) or BLOCKLISTTHDIC[second_far_list[1]]!=1):
                            return (3,distance_list[1][0])
                        #距离次之的两个单元格都是障碍物，飞不了
                        else:
                            return (0,None)
                    #距离最远的单元格是障碍，飞不了
                    else:
                        return (0,None)
            #如果第二名是障碍，那一格飞不了
            else:
                return (0,None)
        #剩余情形
        else:
            return (0,None)

    def make_decision_before_fly(self):
        #飞之前先获取拍卖结果，以决定可能的未来飞行方向
        auction_result=list(self.auction().items())
        #将拍卖结果按照拍卖价格降序，考虑了飞行方向
        if self.orientation == (0, -1):
            num_dic = {1: 1, 2: 2, 4: 3, 3: 4}
            auction_result.sort(key=lambda x: num_dic[x[0]])
            auction_result.sort(key=lambda x: x[1], reverse=True)
        elif self.orientation == (1, 0):
            num_dic = {2: 1, 1: 2, 3: 3, 4: 4}
            auction_result.sort(key=lambda x: num_dic[x[0]])
            auction_result.sort(key=lambda x: x[1], reverse=True)
        elif self.orientation == (-1, 0):
            num_dic = {4: 1, 1: 2, 3: 3, 2: 4}
            auction_result.sort(key=lambda x: num_dic[x[0]])
            auction_result.sort(key=lambda x: x[1], reverse=True)
        else:
            num_dic = {3: 1, 2: 2, 4: 3, 1: 4}
            auction_result.sort(key=lambda x: num_dic[x[0]])
            auction_result.sort(key=lambda x: x[1], reverse=True)
        assert self.orientation in [(0,-1),(-1,0),(0,1),(1,0)]
        print('无人机'+str(self.ID)+'拍卖结果：')
        for module_number,value in auction_result:
            print(str(module_number)+'号模块:'+str(value))
        flag=0
        #最多试四次,看看能不能起飞
        for i in range(4):
            #获得可能的未来飞行方向，这里用自带的字典索引了一下飞行的方向
            orientation=self.orientation_dic[auction_result[i][0]]
            num_can_fly=self.straight_num_can_fly(orientation)
            #如果可以直飞三个格子
            if num_can_fly==3:
                target_pos = (self.pos[0] + 3 * orientation[0], self.pos[1] + 3 * orientation[1])
                target_module_center=self.calc_module_center(pos_new=target_pos,orientation_new=orientation)
                decision=(self.ID,"直飞",target_module_center,i+1)
                #准许起飞
                flag=1
            #如果可以直飞两个格子
            if num_can_fly==2:
                target_pos=(self.pos[0] + 2*orientation[0], self.pos[1] + 2*orientation[1])
                target_module_center=self.calc_module_center(pos_new=target_pos,orientation_new=orientation)
                decision=(self.ID,"直飞",target_module_center,i+1)
                #准许起飞
                flag=1
            #如果可以直飞一个格子，此时一定飞到了不同的模块中
            elif num_can_fly==1:
                target_pos=(self.pos[0] + orientation[0], self.pos[1] + orientation[1])
                target_module_center=self.calc_module_center(pos_new=target_pos,orientation_new=orientation)
                decision=(self.ID,"直飞",target_module_center,i+1)
                #准许起飞
                flag=1
            #如果一个能直飞的格子都没有的话，再考虑一下转弯的情形
            elif num_can_fly==0:
                #如果说转弯可以飞的话
                if self.turn_num_can_fly(orientation)[0]>0:
                    target_pos=self.turn_num_can_fly(orientation)[1]
                    target_module_center = self.calc_module_center(pos_new=target_pos, orientation_new=orientation)
                    decision = (self.ID, "拐弯", target_module_center, i + 1)
                    flag=1
                #转弯也飞不了的话，换个模块再试试
                else:
                    pass
            #一旦准许起飞，跳出循环
            if flag==1:
                break
        #尝试完四个方向，连一个可以飞的模块都没有，如果不是初始化时就这样，则决定退回
        if flag==0:
            #初始化的时候就四面有障碍的情形，无人机决定睡眠
            if self.step==0:
                target_module_center=self.module_center
                decision =(self.ID,"睡眠",target_module_center,0)
            #无人机决定退回
            else:
                target_module_center=self.history_states[-2][2]
                decision=(self.ID,"退回",target_module_center,5)
        global DECISIONS
        DECISIONS.append(decision)

    def straight_show(self,orientation, num_can_fly):
        if num_can_fly!=0:
            if orientation == (0, 1):
                print("向↓飞" + str(num_can_fly) + "格")
            elif orientation == (1, 0):
                print("向→飞" + str(num_can_fly) + "格")
            elif orientation == (-1, 0):
                print("向←飞" + str(num_can_fly) + "格")
            else:
                print("向↑飞" + str(num_can_fly) + "格")
        else:
            if orientation==(1,0):
                print('→堵住了，考虑拐弯')
            elif orientation==(-1,0):
                print('←堵住了，考虑拐弯')
            elif orientation==(0,-1):
                print('↑堵住了，考虑拐弯')
            else:
                print('↓堵住了，考虑拐弯')

    def change_properities(self,orientation, num_can_fly, turn=False):
        if turn == False:
            # 不转弯的话，所在位置的更新
            self.pos = (self.pos[0] + num_can_fly * orientation[0], self.pos[1] + num_can_fly * orientation[1])
        else:
            # 转弯的话，会在函数调用之前手动更新位置
            pass
        # 更新飞行方向
        self.orientation = orientation
        # 无人机之前所在的模块中所有的单元格会变成障碍物，更新两个与障碍物相关的字典，这件事要在无人机所在模块中心点坐标更新之前做
        # 改之前要声明全局变量
        global BLOCKLISTDIC
        global BLOCKLISTTHDIC
        BLOCKLISTDIC[(self.module_center[0] - 0.5, self.module_center[1] - 0.5)] = 5
        BLOCKLISTDIC[(self.module_center[0] + 0.5, self.module_center[1] - 0.5)] = 5
        BLOCKLISTDIC[(self.module_center[0] - 0.5, self.module_center[1] + 0.5)] = 5
        BLOCKLISTDIC[(self.module_center[0] + 0.5, self.module_center[1] + 0.5)] = 5
        BLOCKLISTTHDIC = transform_dic_to_thdic(BLOCKLISTDIC)
        # 更新所在模块中心点坐标
        self.module_center = self.calc_module_center(self.pos, self.orientation)
        # 记录当前所在模块的障碍物分布情况(有可能会超出范围)
        self.photo = self.take_pohto()
        # 更新邻居模块所含单元格位置
        self.neibour_unit_pos = self.get_unit_from_neighbour_module()
        # mode不变
        self.mode = 1
        # 飞行衰减的电量
        self.battery -= num_can_fly
        # 飞行总路程增加
        self.distance += num_can_fly
        # 所处的步数+1
        self.step += 1
        current_state = (self.pos, self.orientation, self.module_center, self.photo,
                         self.neighbour_module_unit_dic, self.mode, self.battery, self.distance, self.step)
        # 黑匣子的修改
        self.black_box.append(current_state)
        # 飞行状态记录器的修改
        self.history_states = self.black_box.copy()

    #根据四个模块的投标结果决定下一步怎么飞
    def fly(self):
        #飞之前先获取拍卖结果，以决定可能的未来飞行方向
        auction_result=list(self.auction().items())
        #将拍卖结果按照拍卖价格降序，考虑了飞行方向
        if self.orientation == (0, -1):
            num_dic = {1: 1, 2: 2, 4: 3, 3: 4}
            auction_result.sort(key=lambda x: num_dic[x[0]])
            auction_result.sort(key=lambda x: x[1], reverse=True)
        elif self.orientation == (1, 0):
            num_dic = {2: 1, 1: 2, 3: 3, 4: 4}
            auction_result.sort(key=lambda x: num_dic[x[0]])
            auction_result.sort(key=lambda x: x[1], reverse=True)
        elif self.orientation == (-1, 0):
            num_dic = {4: 1, 1: 2, 3: 3, 2: 4}
            auction_result.sort(key=lambda x: num_dic[x[0]])
            auction_result.sort(key=lambda x: x[1], reverse=True)
        else:
            num_dic = {3: 1, 2: 2, 4: 3, 1: 4}
            auction_result.sort(key=lambda x: num_dic[x[0]])
            auction_result.sort(key=lambda x: x[1], reverse=True)
        assert self.orientation in [(0,-1),(-1,0),(0,1),(1,0)]
        print('拍卖结果：')
        for module_number,value in auction_result:
            print(str(module_number)+'号模块:'+str(value))
        #起飞许可标志位
        flag=0

        #最多试四次,看看能不能起飞
        for i in range(4):
            #获得可能的未来飞行方向，这里用自带的字典索引了一下飞行的方向
            orientation=self.orientation_dic[auction_result[i][0]]
            num_can_fly=self.straight_num_can_fly(orientation)
            #如果可以直飞三个格子
            if num_can_fly==3:
                self.straight_show(orientation,num_can_fly)
                self.change_properities(orientation,num_can_fly)
                #已经是下一步了
                print()
                print('step：' + str(self.step) + ' 航拍结果:' + str(self.photo))
                #准许起飞
                flag=1
            #如果可以直飞两个格子
            if num_can_fly==2:
                self.straight_show(orientation,num_can_fly)
                self.change_properities(orientation,num_can_fly)
                #已经是下一步了
                print()
                print('step：' + str(self.step) + ' 航拍结果:' + str(self.photo))
                #准许起飞
                flag=1
            #如果可以直飞一个格子，此时一定飞到了不同的模块中
            elif num_can_fly==1:
                self.straight_show(orientation,num_can_fly)
                self.change_properities(orientation,num_can_fly)
                #已经是下一步了
                print()
                print('step：' + str(self.step) + ' 航拍结果:' + str(self.photo))
                #准许起飞
                flag=1
            #如果一个能直飞的格子都没有的话，再考虑一下转弯的情形
            elif num_can_fly==0:
                self.straight_show(orientation,num_can_fly)
                #如果说转弯可以飞的话
                if self.turn_num_can_fly(orientation)[0]>0:
                    self.pos=self.turn_num_can_fly(orientation)[1]
                    self.change_properities(orientation, num_can_fly,turn=True)
                    print('转弯')
                    # 已经是下一步了
                    print()
                    print('step：' + str(self.step) + ' 航拍结果:' + str(self.photo))
                    flag=1
                #转弯也飞不了的话，换个模块再试试
                else:
                    pass
            #一旦准许起飞，跳出循环
            if flag==1:
                break

        #尝试完四个方向，连一个可以飞的模块都没有，如果不是初始化时就这样，则决定退回
        if flag==0:
            #排除初始化的时候就四面有障碍的情形
            if self.step==0:
                print('无人机'+str(self.ID)+'无法起飞，进入睡眠模式！')
                #只需要修改mode为0
                self.mode=0
                self.step+=1
                current_state=(self.pos, self.orientation, self.module_center,self.photo,self.neighbour_module_unit_dic,self.mode, self.battery, self.distance, self.step)
                self.black_box.append(current_state)
                self.history_states=self.black_box.copy()
                return 200
            #无人机决定退回
            else:
                print('无人机'+str(self.ID)+'退回')
                #无人机当前所在的模块中所有的单元格会变成障碍物，更新两个与障碍物相关的字典，这件事要在无人机所在模块中心点坐标更新之前做
                global BLOCKLISTDIC,BLOCKLISTTHDIC
                BLOCKLISTDIC[(self.module_center[0]-0.5,self.module_center[1]-0.5)]=5
                BLOCKLISTDIC[(self.module_center[0]+0.5,self.module_center[1]-0.5)]=5
                BLOCKLISTDIC[(self.module_center[0]-0.5,self.module_center[1]+0.5)]=5
                BLOCKLISTDIC[(self.module_center[0]+0.5,self.module_center[1]+0.5)]=5
                BLOCKLISTTHDIC=transform_dic_to_thdic(BLOCKLISTDIC)
                #飞机自身的属性进行修改
                num=abs(self.pos[0]-self.history_states[-2][0][0])+abs(self.pos[1]-self.history_states[-2][0][1])
                self.pos=self.history_states[-2][0]
                self.orientation=self.history_states[-2][1]
                self.module_center=self.history_states[-2][2]
                self.photo=self.history_states[-2][3]
                self.neibour_unit_pos = self.get_unit_from_neighbour_module()
                self.mode=self.history_states[-2][5]
                self.battery-=num
                self.distance+=num
                self.step+=1
                current_state=(self.pos,self.orientation,self.module_center,self.photo,
                               self.neighbour_module_unit_dic,self.mode,self.battery,self.distance,self.step)
                self.black_box.append(current_state)
                self.history_states.pop()
                #恢复无人机之前所在模块的障碍物分布情况
                BLOCKLISTDIC[(self.module_center[0]-0.5,self.module_center[1]-0.5)]=self.photo[(self.module_center[0]-0.5,self.module_center[1]-0.5)]
                BLOCKLISTDIC[(self.module_center[0]+0.5,self.module_center[1]-0.5)]=self.photo[(self.module_center[0]+0.5,self.module_center[1]-0.5)]
                BLOCKLISTDIC[(self.module_center[0]-0.5,self.module_center[1]+0.5)]=self.photo[(self.module_center[0]-0.5,self.module_center[1]+0.5)]
                BLOCKLISTDIC[(self.module_center[0]+0.5,self.module_center[1]+0.5)]=self.photo[(self.module_center[0]+0.5,self.module_center[1]+0.5)]
                BLOCKLISTTHDIC=transform_dic_to_thdic(BLOCKLISTDIC)
                print()
                print('step：' + str(self.step) + ' 航拍结果:' + str(self.photo))
                return 300

#冲突判断函数
def conflict():
    global DECISIONS
    #把所有的目标模块中心点取出来
    target_module_centers=[]
    for decision in DECISIONS:
        target_module_centers.append(decision[2])
    #把具有相同目标模块中心点的决定 单独拿出来进行冲突检测分析
    same_target_dic = {}
    for decision in DECISIONS:
        if target_module_centers.count(decision[2])>=2:
            same_target_dic[decision[2]]=[]
    for decision in DECISIONS:
        if target_module_centers.count(decision[2])>=2:
            same_target_dic[decision[2]].append([decision[0],decision[1],decision[3]])
    #做最终决定了，没有冲突的飞机保持原样
    final_decisions_dic={}
    for decision in DECISIONS:
        if decision[2] not in same_target_dic:
            final_decisions_dic[decision[0]]=decision[1:-1]
    #产生冲突的飞机只能飞一架，其它的飞机的策略需要修改
    for target_module_center in same_target_dic:
        same_target_dic[target_module_center].sort(key=lambda x:eval('uav'+str(x[0])+'.distance'),reverse=False)
        final_decisions_dic[same_target_dic[target_module_center][0][0]]=(same_target_dic[target_module_center][0][1],same_target_dic[target_module_center][0][2])
        i=1
        while i<len(same_target_dic[target_module_center]):
            if same_target_dic[target_module_center][i][2]==1:
                final_decisions_dic[same_target_dic[target_module_center][i][0]]=(None,2)
            elif same_target_dic[target_module_center][i][2]==2:
                final_decisions_dic[same_target_dic[target_module_center][i][0]]=(None,3)
            elif same_target_dic[target_module_center][i][2]==3:
                final_decisions_dic[same_target_dic[target_module_center][i][0]]=(None,4)
            elif same_target_dic[target_module_center][i][2]==4:
                final_decisions_dic[same_target_dic[target_module_center][i][0]]=(None,5)
            i+=1
    return final_decisions_dic

#该函数绘制障碍物和多无人机位置、所在模块中心点、搜索半径、航迹，不会改变全局变量
def show_block_and_uavs(i,uavs):
    pygame.display.set_caption('PASS算法演示，第' + str(i) + '步')
    # 障碍物的像素坐标
    blocklistdic_pix = {}
    for pos in BLOCKLISTDIC:
        th = BLOCKLISTDIC[pos]
        x_pix, y_pix = pos[0] * CELL_WIDTH, pos[1] * CELL_HEIGHT
        blocklistdic_pix[(x_pix, y_pix)] = th
    bl_pix = list(blocklistdic_pix.keys())
    assert len(bl_pix)==len(BLOCKLISTDIC)
    REACHABLELIST = []
    for (x, y) in m.generate_cell():
        if (x, y) in bl_pix:
            if blocklistdic_pix[(x, y)] == 1:
                # 绘制障碍物单元格，并留出2个像素的边框
                pygame.draw.rect(screen, COLOR_TH1, (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
            elif blocklistdic_pix[(x, y)] == 2:
                pygame.draw.rect(screen, COLOR_TH2, (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
            elif blocklistdic_pix[(x, y)] == 3:
                pygame.draw.rect(screen, COLOR_TH3, (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
            elif blocklistdic_pix[(x, y)] == 4:
                pygame.draw.rect(screen, COLOR_TH4, (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
            elif blocklistdic_pix[(x, y)] == 5:
                pygame.draw.rect(screen, COLOR_TH5, (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
            # 绘制可通行单元格，并留出2个像素的边框
            else:
                if (x // CELL_WIDTH, y // CELL_HEIGHT) not in REACHABLELIST:
                    REACHABLELIST.append((x // CELL_WIDTH, y // CELL_HEIGHT))
                pygame.draw.rect(screen, THECOLORS['white'], (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH),
                    (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
        else:
            # 绘制可通行单元格，并留出2个像素的边框
            if (x // CELL_WIDTH, y // CELL_HEIGHT) not in REACHABLELIST:
                REACHABLELIST.append((x // CELL_WIDTH, y // CELL_HEIGHT))
            pygame.draw.rect(screen, THECOLORS['white'], (
                (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
    for uav in uavs:
        #加载无人机图标
        imgRect = pygame.image.load(uav.pic_path)
        screen.blit(imgRect, (uav.pos[0] * CELL_WIDTH, uav.pos[1] * CELL_HEIGHT))
        #无人机模块中心点绘制
        pygame.draw.circle(screen, THECOLORS['red'],
                           [(uav.module_center[0] + 0.5) * CELL_WIDTH, (uav.module_center[1] + 0.5) * CELL_HEIGHT], 3, 0)
        # 测试模式下绘制出无人机的搜索半径
        if uav.test_mode:
            unit_from_neighbour_module_pix = transform_lst(uav.neibour_unit_pos)
            for (x, y) in unit_from_neighbour_module_pix:
                pygame.draw.circle(screen, THECOLORS['yellow'],
                                   [x + 0.5 * CELL_WIDTH, y + 0.5 * CELL_HEIGHT], 3, 0)
        #绘制航迹
        if i!=0:
            TRAJECTORYS["uav"+str(uav.ID)].append(uav.pos)
            pygame.draw.aalines(screen, THECOLORS['black'], False, transform_lst_point(TRAJECTORYS["uav"+str(uav.ID)]))
        pygame.display.flip()
    #保存图片
    pygame.image.save(screen, "pass" + str(i) + ".jpg")
    pygame.time.wait(2000)

if __name__=='__main__':
    #地图初始化
    m=Map(((MAPSIZE[0]+2)*CELL_WIDTH,(MAPSIZE[1]+2)*CELL_HEIGHT))
    #产生所有的障碍物
    BLOCKLISTDIC=gen_blocks()
    print('BLOCKLISTDIC:',BLOCKLISTDIC)
    #产生记录了障碍物威胁程度与位置坐标的字典
    BLOCKLISTTHDIC = transform_dic_to_thdic(BLOCKLISTDIC)
    print('BLOCKLISTTHDIC:', BLOCKLISTTHDIC)
    print()
    reachablelist=[]
    for i in m.generate_cell():
        if (i[0]//CELL_WIDTH,i[1]//CELL_HEIGHT) not in BLOCKLISTDIC:
            reachablelist.append((i[0]//CELL_WIDTH,i[1]//CELL_HEIGHT))
    assert len(reachablelist)==(MAPSIZE[0]+2)*(MAPSIZE[1]+2)-len(BLOCKLISTTHDIC)

    #多架uav初始化
    reachablelist_init1=[]
    for item in reachablelist:
        if item[0]==1:
            reachablelist_init1.append(item)
    random_index_list1 = random.sample(range(0,len(reachablelist_init1)),3)
    INIT_POS1 = reachablelist_init1[random_index_list1[0]]
    INIT_POS2 = reachablelist_init1[random_index_list1[1]]
    print(random_index_list1)
    INIT_POS3 = reachablelist_init1[random_index_list1[2]]
    uav1=UAV(1,[6,3],)
    uav2=UAV(2,[5,4],)
    uav3=UAV(3,[6,5],)

    reachablelist_init2=[]
    for item in reachablelist:
        if item[0]==MAPSIZE[0]:
            reachablelist_init2.append(item)
    random_index_list2 = random.sample(range(0,len(reachablelist_init2)),3)
    INIT_POS4 = reachablelist_init2[random_index_list2[0]]
    INIT_POS5 = reachablelist_init2[random_index_list2[1]]
    INIT_POS6 = reachablelist_init2[random_index_list2[2]]
    uav4=UAV(4,[7,4],)
    # uav5=UAV(5,INIT_POS5,)
    # uav6=UAV(6,INIT_POS6,)

    reachablelist_init3=[]
    for item in reachablelist:
        if item[1]==1:
            reachablelist_init3.append(item)
    random_index_list3 = random.sample(range(0,len(reachablelist_init3)),3)
    INIT_POS7 = reachablelist_init3[random_index_list3[0]]
    INIT_POS8 = reachablelist_init3[random_index_list3[1]]
    INIT_POS9 = reachablelist_init3[random_index_list3[2]]
    # uav7=UAV(7,INIT_POS7,)
    # uav8=UAV(8,INIT_POS8,)
    # uav9=UAV(9,INIT_POS9,)

    reachablelist_init4=[]
    for item in reachablelist:
        if item[1]==MAPSIZE[1]:
            reachablelist_init4.append(item)
    random_index_list4 = random.sample(range(0,len(reachablelist_init3)),3)
    INIT_POS10 = reachablelist_init4[random_index_list4[0]]
    INIT_POS11 = reachablelist_init4[random_index_list4[1]]
    INIT_POS12 = reachablelist_init4[random_index_list4[2]]
    # uav10=UAV(10,INIT_POS10,)
    # uav11=UAV(11,INIT_POS11,)
    # uav12=UAV(12,INIT_POS12,)
    #多无人机列表
    uavs=[uav1,uav2,uav3,uav4]
    #pygame初始化
    pygame.init()
    screen = pygame.display.set_mode(m.map_pixsize)
    screen.fill([192, 192, 192])
    #显示障碍物和多无人机相关
    show_block_and_uavs(0,uavs)
    #多无人机航迹初始化
    TRAJECTORYS={'uav1':[INIT_POS1],'uav2':[INIT_POS2],'uav3':[INIT_POS3],'uav4':[INIT_POS4]}

    for uav in uavs:
        print(uav.make_decision_before_fly())
    uav1_make_decision_thread=threading.Thread(target=uav1.make_decision_before_fly)
    uav2_make_decision_thread=threading.Thread(target=uav2.make_decision_before_fly)
    uav3_make_decision_thread=threading.Thread(target=uav3.make_decision_before_fly)
    uav4_make_decision_thread=threading.Thread(target=uav4.make_decision_before_fly)
    uav1_make_decision_thread.start()
    uav2_make_decision_thread.start()
    uav3_make_decision_thread.start()
    uav4_make_decision_thread.start()
    threads = [uav1_make_decision_thread,uav2_make_decision_thread,uav3_make_decision_thread,uav4_make_decision_thread]
    for t in threads:
        t.join()
    print(DECISIONS)
    # uav1_fly_thread.start()
    # uav2_fly_thread.start()
    # uav3_fly_thread.start()
    # uav4_fly_thread.start()
    # for i in range(1,501):
    #     uav1_fly_thread=threading.Thread(target=uav1.fly)
    #     uav2_fly_thread=threading.Thread(target=uav2.fly)
    #     uav3_fly_thread=threading.Thread(target=uav3.fly)
    #     uav4_fly_thread=threading.Thread(target=uav4.fly)
    #     uav5_fly_thread = threading.Thread(target=uav5.fly)
    #     uav6_fly_thread = threading.Thread(target=uav6.fly)
    #     uav7_fly_thread = threading.Thread(target=uav7.fly)
    #     uav8_fly_thread=threading.Thread(target=uav8.fly)
    #     uav9_fly_thread=threading.Thread(target=uav9.fly)
    #     uav10_fly_thread=threading.Thread(target=uav10.fly)
    #     uav11_fly_thread=threading.Thread(target=uav11.fly)
    #     uav12_fly_thread=threading.Thread(target=uav12.fly)
    #     threads=[uav1_fly_thread,uav2_fly_thread,uav3_fly_thread,uav4_fly_thread,uav5_fly_thread,uav6_fly_thread,uav7_fly_thread,uav8_fly_thread,
    #              uav10_fly_thread,uav11_fly_thread,uav12_fly_thread,uav9_fly_thread,]
    #     uav1_fly_thread.start()
    #     uav2_fly_thread.start()
    #     uav3_fly_thread.start()
    #     uav4_fly_thread.start()
    #     uav5_fly_thread.start()
    #     uav6_fly_thread.start()
    #     uav7_fly_thread.start()
    #     uav8_fly_thread.start()
    #     uav9_fly_thread.start()
    #     uav10_fly_thread.start()
    #     uav12_fly_thread.start()
    #     uav11_fly_thread.start()
    #     for t in threads:
    #         t.join()
    #     TRAJECTORYS['uav1'].append(uav1.pos)
    #     TRAJECTORYS['uav2'].append(uav2.pos)
    #     TRAJECTORYS['uav3'].append(uav3.pos)
    #     TRAJECTORYS['uav4'].append(uav4.pos)
    #     TRAJECTORYS['uav5'].append(uav5.pos)
    #     TRAJECTORYS['uav6'].append(uav6.pos)
    #     TRAJECTORYS['uav7'].append(uav7.pos)
    #     TRAJECTORYS['uav8'].append(uav8.pos)
    #     TRAJECTORYS['uav9'].append(uav9.pos)
    #     TRAJECTORYS['uav10'].append(uav10.pos)
    #     TRAJECTORYS['uav11'].append(uav11.pos)
    #     TRAJECTORYS['uav12'].append(uav12.pos)
    #
    #     show_block_and_uavs(i, uavs)
    #飞和显示(该飞的飞，该退的退，最后显示一下)
    # for i in range(1,1000):
    #     #所有的无人机都先飞一格
    #     for uav in uavs:
    #         uav.fly()
    #         #航迹先加上去
    #         TRAJECTORYS['uav'+str(uav.ID)].append(uav.pos)
    #     #如果出现了多架无人机位于同一模块的情形，则修改冲突标志位CONFLICT_FLAG为1
    #     #同时返回的总路程多的无人机ID列表
    #     if conflict():
    #         CONFLICT_FLAG=1
    #         conflict_ID_list=conflict()
    #         #把冲突飞机的航迹给扣除了
    #         for id in conflict_ID_list:
    #             TRAJECTORYS['uav'+str(id)].pop()
    #     #冲突的无人机会退回，其它无人机不动
    #     if CONFLICT_FLAG==1:
    #         for uav in uavs:
    #             if uav.ID in conflict_ID_list:
    #                 uav.back()
    #                 #把退回的航迹加上去
    #                 TRAJECTORYS['uav' + str(uav.ID)].append(uav.pos)
    #     #冲突标志位改回0
    #     CONFLICT_FLAG=0
    #     #显示
    #     show_block_and_uavs(i,uavs)
    # mRunning = True
    # while mRunning:
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             mRunning = False
    # pygame.quit()
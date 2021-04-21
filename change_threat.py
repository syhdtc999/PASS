import pygame
from pygame.color import THECOLORS
from random import randint
import numpy as np

#地图大小
MAPSIZE=(12,12)
#障碍物总数
BLOCK_NUM=15
#三种不同范围的权重
WEIGHT1 = 0.05
WEIGHT2 = 0.7
WEIGHT3 = 0.25
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
    # realblocklist.append((9,1))
    # realblocklist.append((9,2))
    # realblocklist.append((9,3))
    # realblocklist.append((8,3))
    # realblocklist.append((7,3))
    # realblocklist.append((7,4))
    # realblocklist.append((7,5))
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

    #其余的威胁等级为0
    for x in range(1,MAPSIZE[0]+1):
        for y in range(1,MAPSIZE[1]+1):
            if (x,y) not in blocklistdic:
                blocklistdic[(x,y)]=0

    return blocklistdic

BLOCKLISTDIC=gen_blocks()
assert len(gen_blocks())==(MAPSIZE[0]+2)*(MAPSIZE[1]+2)
print(BLOCKLISTDIC)

def random_change_blocks():
    global BLOCKLISTDIC
    blocks_have_changed=set()
    for block in BLOCKLISTDIC:
        if BLOCKLISTDIC[block]==5:
            pass
        elif BLOCKLISTDIC[block]==4:
            if block not in blocks_have_changed:
                m=randint(-1,1)
                new_pos=(block[0]+m,block[1]+m)
                #新位置必须合法
                if 1<=new_pos[0]<=MAPSIZE[0] and 1<=new_pos[1]<=MAPSIZE[1]:
                    if BLOCKLISTDIC[new_pos]<=4:
                        BLOCKLISTDIC[block]=BLOCKLISTDIC[new_pos]
                        BLOCKLISTDIC[new_pos]=4
                        blocks_have_changed.add(new_pos)
                        blocks_have_changed.add(block)
        elif BLOCKLISTDIC[block]==3:
            if block not in blocks_have_changed:
                m=randint(-2,2)
                new_pos=(block[0]+m,block[1]+m)
                if 1 <= new_pos[0] <= MAPSIZE[0] and 1 <= new_pos[1] <= MAPSIZE[1]:
                    if BLOCKLISTDIC[new_pos]<=3:
                        BLOCKLISTDIC[block]=BLOCKLISTDIC[new_pos]
                        BLOCKLISTDIC[new_pos]=3
                        blocks_have_changed.add(new_pos)
                        blocks_have_changed.add(block)
        elif BLOCKLISTDIC[block]==2:
            if block not in blocks_have_changed:
                m=randint(-3,3)
                new_pos=(block[0]+m,block[1]+m)
                if 1 <= new_pos[0] <= MAPSIZE[0] and 1 <= new_pos[1] <= MAPSIZE[1]:
                    if BLOCKLISTDIC[new_pos]<=2:
                        BLOCKLISTDIC[block]=BLOCKLISTDIC[new_pos]
                        BLOCKLISTDIC[new_pos]=2
                        blocks_have_changed.add(new_pos)
                        blocks_have_changed.add(block)
        elif BLOCKLISTDIC[block]==1:
            if block not in blocks_have_changed:
                m=randint(-4,4)
                new_pos=(block[0]+m,block[1]+m)
                if 1 <= new_pos[0] <= MAPSIZE[0] and 1 <= new_pos[1] <= MAPSIZE[1]:
                    if BLOCKLISTDIC[new_pos]<=1:
                        BLOCKLISTDIC[block]=BLOCKLISTDIC[new_pos]
                        BLOCKLISTDIC[new_pos]=1
                        blocks_have_changed.add(new_pos)
                        blocks_have_changed.add(block)
        elif BLOCKLISTDIC[block]==0:
            pass

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


def show_block_and_uav(i):
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

                pygame.draw.rect(screen, [255,255,255], (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
                imgRect = pygame.image.load("1.png")
                screen.blit(imgRect, (x , y ))
            elif blocklistdic_pix[(x, y)] == 2:
                pygame.draw.rect(screen, [255,255,255], (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
                imgRect = pygame.image.load("2.png")
                screen.blit(imgRect, (x , y ))
            elif blocklistdic_pix[(x, y)] == 3:
                pygame.draw.rect(screen, [255,255,255], (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
                imgRect = pygame.image.load("3.png")
                screen.blit(imgRect, (x , y ))
            elif blocklistdic_pix[(x, y)] == 4:
                pygame.draw.rect(screen, [255,255,255], (
                    (x + BORDER_WIDTH, y + BORDER_WIDTH), (CELL_WIDTH - 2 * BORDER_WIDTH, CELL_HEIGHT - 2 * BORDER_WIDTH)))
                imgRect = pygame.image.load("4.png")
                screen.blit(imgRect, (x , y ))
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

    pygame.display.flip()
    #保存图片
    pygame.image.save(screen, "pass" + str(i) + ".jpg")
    pygame.time.wait(2000)

def check():
    count0=0
    count1=0
    count2=0
    count3=0
    count4=0
    count5=0
    for block in BLOCKLISTDIC:
        if BLOCKLISTDIC[block]==0:
            count0+=1
        elif BLOCKLISTDIC[block]==1:
            count1+=1
        elif BLOCKLISTDIC[block]==2:
            count2+=1
        elif BLOCKLISTDIC[block]==3:
            count3+=1
        elif BLOCKLISTDIC[block]==4:
            count4+=1
        elif BLOCKLISTDIC[block]==5:
            count5+=1
    print("0:"+str(count0)+"个,1:"+str(count1)+"个,2:"+str(count2)+"个,3:"+str(count3)+"个,4:"+str(count4)+"个,5:"+str(count5)+"个")
    assert count5+count4+count3+count2+count1+count0==(MAPSIZE[0]+2)*(MAPSIZE[1]+2)
if __name__ == '__main__':
    m=Map(((MAPSIZE[0]+2)*CELL_WIDTH,(MAPSIZE[1]+2)*CELL_HEIGHT))
    pygame.init()
    screen = pygame.display.set_mode(m.map_pixsize)
    screen.fill([192, 192, 192])
    for i in range(20):
        show_block_and_uav(i)
        check()
        random_change_blocks()
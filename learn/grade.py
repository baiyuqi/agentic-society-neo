
c1='''78
83
77
88
78
73
80
82
84
89
80
78
78
64
85
85
80
73
85
78
79
82
89
87
33
78
85
68
83
61
80
61
57'''
c2='''88
88
80
82
85
93
93
70
79
61
87
53
81
92
94
88
96
81
94
98
60
86
87
77
88
64
76
83
72
82
77
75
61
57
78'''
grade='''78
83
77
88
78
73
80
82
84
89
80
78
78
64
85
85
80
73
85
78
79
82
89
87
33
78
85
68
83
61
80
61
57
88
88
80
82
85
93
93
70
79
61
87
53
81
92
94
88
96
81
94
98
60
86
87
77
88
64
76
83
72
82
77
75
61
57
78'''

def stat(data):
    gs = data.split('\n')
    gs = [float(g) for g in gs]

    level = [int(l/10) for l in gs]
    count = {3:0, 4:0,5:0, 6:0, 7:0,8:0,9:0,10:0}
    for x in level:
        c = count[x]
        count[x] = c + 1
    for k in count.keys():
        c = count[k]
        v = 100* c/len(gs)
        count[k] = (c, v)
    return count
import pandas as pd
x = [stat(c1),stat(c2),stat(grade)]
pdf0 = pd.DataFrame(x[0])
pdf1 = pd.DataFrame(x[1])
pdf2 = pd.DataFrame(x[2])
print(pdf0)
print(pdf1)
print(pdf2)
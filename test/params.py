import argparse

data = {"id":1,"ia1":2}
ll= [data]
aa= []
aa.extend(ll)
aa.extend(ll)
aa.extend(ll)
print(ll)
print(aa[0].get("id123"))
aas={}
aas["as"]=1
print(aas)
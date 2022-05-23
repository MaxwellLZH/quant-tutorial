# 微信号：15815705123

from jqdatasdk import *

from config import jq_account

# auth_result = auth(jq_account['name'], jq_account['password'])
auth_result = auth('13585754438', 'Womeiyoumima12345!')

print(auth_result)


codes = get_all_securities(types=['futures'], date=None)
print(codes)
from pathlib import Path
import os

LOCAL_DIR = Path(__file__).parent
ROOT_DIR = LOCAL_DIR.parent
CODE_DIR = ROOT_DIR / 'code'
SRC_DIR = ROOT_DIR / 'src'
OUTPUT_DIR = ROOT_DIR / 'reading_material'
README_FILE = ROOT_DIR / 'README.md'


with open(LOCAL_DIR / 'README_template.md') as f:
	template = f.read()


content = list()

# 遍历reading_material下的文件
for f in SRC_DIR.glob('*.md'):
	# ex. 量化指标
	topic_name = f.name.replace('.md', '')
	content.append('## {}'.format(topic_name))

	sub_topic, topic_content, readme = None, [], []
	with open(f, 'r') as i:
		for line in i:
			if line.startswith(r'###'):
				# 为这个topic创建独立的README文件
				if sub_topic is not None:
					readme.append(f'# {sub_topic}')
					readme.append(f'## 介绍')
					readme.extend(topic_content)

					# 找对应的代码文件
					

					readme.append(f'## 代码')

					path = OUTPUT_DIR / topic_name / (sub_topic.replace(' ', '') + '.md')
					try:
						os.makedirs(path.parent)
					except:
						pass

					with open(path, 'w') as r:
						r.write('\n'.join(readme))


				sub_topic = line.replace(r'###', '').strip()
				link = f'/reading_material/{topic_name}/{sub_topic.replace(" ", "")}.md'
				content.append(f'- [{sub_topic}]({link})')
			else:
				topic_content.append(line)




# 替换template
readme = template.replace('CONTENT', '  \n'.join(content))
print(readme)

with open(README_FILE, 'w', encoding='utf8') as f:
	f.write(readme)

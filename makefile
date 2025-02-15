all:
		curl https://amirouche.dev/ | html2text --ignore-links | grep '## ' | head -n 5 | tail -n 4 > README.body.md
		cat README.head.md README.body.md README.foot.md > README.md

all:
		curl https://amirouche.dev/ | python3 -m html2text --ignore-links | grep '## ' | head -n 5 | tail -n 4 | sed -e 's/## /- /g' > README.body.md
		cat README.head.md README.body.md README.foot.md > README.md

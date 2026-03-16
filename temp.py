import jieba




# fenci 

txt = '''
美国和以色列对伊朗发动的军事打击16日进入第17天。美国媒体15日披露，美国拟宣布组建霍尔木兹海峡“护航联盟”。同日，伊朗发布战报，警告打击“福特”号航母后勤。伊朗外长阿拉格齐表示，伊朗从未请求美国停火，甚至没有请求谈判。伊朗最高领袖重申“将向敌人索赔”。
'''

lst_txt = jieba.cut(txt)
list(lst_txt)




# emotion

# download sentiemnt score:
# https://github.com/flingjie/words_image/blob/master/sentiment/BosonNLP_sentiment_score.txt



class WordSentimentAnalyzer:
    def __init__(self, dict_path: str = "BosonNLP_sentiment_score.txt"):
        
        self.sentiment_dict = self._load_dict(dict_path)
    
    def _load_dict(self, dict_path: str) -> dict:
        
        sentiment_dict = {}
        try:
            with open(dict_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    word = " ".join(parts[:-1])
                    score = float(parts[-1])
                    sentiment_dict[word] = score
            print(f"成功加载 {len(sentiment_dict)} 个情感词语")
        except FileNotFoundError:
            raise FileNotFoundError(f"词典文件未找到：{dict_path}")
        return sentiment_dict
    
    def get_word_sentiment(self, word: str) -> dict:
        
        word = word.strip()
        
        score = self.sentiment_dict.get(word, 0.0)
        
        
        if score > 0:
            label = "正面"
        elif score < 0:
            label = "负面"
        else:
            label = "中性"
        
        return {
            "词语": word,
            "情感分值": score,
            "情感标签": label
        }
    
    def analyze_sentence_words(self, sentence: str) -> list:
        
        words = jieba.lcut(sentence, cut_all=False)
        
        unique_words = list(filter(None, set(words)))
        
        results = [self.get_word_sentiment(word) for word in unique_words]
        return results



analyzer = WordSentimentAnalyzer(dict_path="C:/Users/tomyi/Downloads/BosonNLP_sentiment_score.txt")


word_results = analyzer.analyze_sentence_words(txt)
for res in word_results:
    print(res) 

    

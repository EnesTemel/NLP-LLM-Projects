import torch
import torch.nn as nn
from torch.nn import functional as F

# hyperparameters
batch_size=64
block_size=256
max_iters=5000
eval_interval=500
learning_rate=3e-4
device='cuda' if torch.cuda.is_available() else 'cpu'
eval_iters=200
n_embd = 384
n_head=6
n_layer=6
dropout=0.2
# -------------

torch.manual_seed(1337)

# wget https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt
with open(r'C:\Users\enesm\OneDrive\Masaüstü\VSCODE\NeuralNetworks\nanoGPT\input.txt','r',encoding='utf-8') as f:
    text = f.read()

chars=sorted(list(set(text)))
vocab_size=len(chars)   

# create the mappings
stoi={ch:i for i,ch in enumerate(chars)}
itos={i:ch for i,ch in enumerate(chars)}
encode= lambda s: [stoi[c] for c in s ]
decode= lambda l: ''.join([itos[i] for i in l ])

# encode / train test split
data=torch.tensor(encode(text),dtype=torch.long)
n=int(0.9*len(data))
train_data=data[:n]
val_data=data[n:]

# data loading
def get_batch(split):
    # generate a small batch of data of inputs x and targets y 
    data = train_data if split == 'train' else val_data
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    x,y=x.to(device),y.to(device)
    return x,y

@torch.no_grad()
def estimate_loss():
    out={}
    model.eval()
    for split in ['train','val']:
        losses=torch.zeros(eval_iters)
        for k in range(eval_iters):
            X,Y= get_batch(split)
            logits,loss = model(X,Y)
            losses[k]=loss.item()
        out[split]=losses.mean()
    model.train()
    return out

class Head(nn.Module):
    
    def __init__(self,head_size):
        super().__init__()
        self.key=nn.Linear(n_embd,head_size,bias=False)
        self.query=nn.Linear(n_embd,head_size,bias=False)
        self.value=nn.Linear(n_embd,head_size,bias=False)
        self.register_buffer('tril',torch.tril(torch.ones(block_size,block_size)))

        self.dropout= nn.Dropout(dropout)
    
    def forward(self,x):
        B,T,C = x.shape
        k = self.key(x) #(B,T,C)
        q = self.query(x) #(B,T,C)
        # compute attention scores('affinities)
        wei=q @ k.transpose(-2,-1)* C**-0.5 #(B,T,C)@ #(B,C,T) --> (B,T,T)
        wei=wei.masked_fill(self.tril[:T,:T] == 0 , float('-inf') )
        wei= F.softmax(wei,dim=-1) # (B,T,T)
        wei= self.dropout(wei)
        v=self.value(x)
        out= wei@v
        return out
    
class MultiHeadAttention(nn.Module):
    "multiple heads of self-attention running in parralel"

    def __init__(self,num_heads,head_size):
        super().__init__()
        self.heads= nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.proj = nn.Linear(n_embd,n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self,x):
        out = torch.cat([h(x) for h in self.heads],dim=-1)
        out = self.dropout(self.proj(out))
        return out
    
class FeedForward(nn.Module):
    
    def __init__(self,n_embd):
        super().__init__()
        self.net=nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.ReLU(),
            nn.Linear(4 * n_embd,n_embd),
            nn.Dropout(dropout),
        )
    
    def forward(self,x):
        return self.net(x)

class Block(nn.Module):
    def __init__(self,n_embd,n_head):
        # n_embd: embeddings dimension, n_head: number of heads we'd like
        super().__init__()
        head_size = n_embd // n_head
        self.sa = MultiHeadAttention(n_head,head_size)
        self.ffwd = FeedForward(n_embd)
        self.ln1 = nn.LayerNorm(n_embd) 
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self,x):
        x = x + self.sa(self.ln1(x)) 
        # In the paper the normalization happens right after the transformation
        # But nowadays we use it right before the transformation it called the "pre-norm formulation"
        x = x + self.ffwd(self.ln2(x))
        return x


# super simple bigram model
class BigramLanguageModel(nn.Module):

    def __init__(self): 
        super().__init__()
        self.token_embedding_table = nn.Embedding(vocab_size,n_embd)
        self.position_embedding_table=nn.Embedding(block_size,n_embd)
        self.blocks = nn.Sequential(*[Block(n_embd,n_head=n_head) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd) 
        self.lm_head= nn.Linear(n_embd,vocab_size)
        
    
    def forward(self,idx,targets=None):
        B,T = idx.shape
        #idx and targets are both (B,T) tensor of integers  
        tok_emb= self.token_embedding_table(idx) # (B,T,C)
        pos_emb=self.position_embedding_table(torch.arange(T,device=device)) # (T,C)
        x = tok_emb + pos_emb # (B,T,C)
        x = self.blocks(x) # (B,T,C)
        logits= self.lm_head(x) # (B,T,vocab_size)


        if targets is None:
            loss=None

        else:
            B,T,C=logits.shape 
            logits=logits.view(B*T,C)
            targets=targets.view(B*T)
            loss= F.cross_entropy(logits, targets)

        return logits,loss
    
    def generate(self,idx,max_new_tokens):

        for _ in range(max_new_tokens):
            #get the predictions
            idx_cond=idx[:,-block_size:]
            logits,loss=self(idx_cond)   
            logits=logits[:,-1,:]
            probs=F.softmax(logits,dim=-1)
            idx_next=torch.multinomial(probs,num_samples=1)
            idx=torch.cat((idx,idx_next), dim=1)
        return idx
    


model=BigramLanguageModel()
m=model.to(device)


#create a PyTorch optimizer
optimizer=torch.optim.AdamW(m.parameters(),lr=learning_rate)

for iter in range(max_iters):
    # every once in a while evaluate
    if iter % eval_interval == 0:
        losses=estimate_loss()
        print(f"step{iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

    # sample a batch of data
    xb,yb=get_batch('train')

    # evaluate loss
    logits,loss=model(xb,yb)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()
  

# generate from the model 
context = torch.zeros((1,1),dtype=torch.long,device=device)
print(decode(m.generate(context,max_new_tokens=500)[0].tolist()))


1.29
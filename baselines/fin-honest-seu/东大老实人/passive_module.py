import torch
import torch.nn as nn
import torch.nn.functional as F
from utils import cards_mapping


class Dan_attention(nn.Module):
    """
    """
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.w_keys = nn.Parameter(torch.Tensor(in_channels, out_channels))
        self.w_values = nn.Parameter(torch.Tensor(in_channels, out_channels))
        self.w_querys = nn.Parameter(torch.Tensor(in_channels, out_channels))
        self._init_parameters()

    def _init_parameters(self):
        torch.nn.init.xavier_uniform_(self.w_keys)
        torch.nn.init.xavier_uniform_(self.w_values)
        torch.nn.init.xavier_uniform_(self.w_querys)

    def forward(self, x):
        keys = x @ self.w_keys
        values = x @ self.w_values
        querys = x @ self.w_querys
        attn_scores = querys @ keys.T
        attn_scores_softmax = F.softmax(attn_scores, dim=-1)
        weighted_values = values[:, None] * attn_scores_softmax.T[:, :, None]
        outputs = weighted_values.sum(dim=0)
        return outputs


class Dan_layer(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.fc1 = nn.Linear(in_channels, 32)
        self.fc2 = nn.Linear(32, out_channels)

    def _init_parameters(self):
        pass

    def forward(self, x):
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        return x


class Dan_passive(nn.Module):
    """
    """
    def __init__(self):
        """
            description :  613 including 405(all kinds of card) +
                           104(rank card dim)
                          + 1(pass)
        """
        super().__init__()
        self.embedding = nn.Embedding(639, 64)
        self.attention_layer = Dan_attention(64, 64)
        self.fc = Dan_layer(128, 64)
        self._init_parameters()

    def _init_parameters(self, ):
        torch.nn.init.xavier_uniform_(self.embedding.weight)

    def forward(self, card, actionList):
        card_embedding = self.embedding(
            torch.tensor(cards_mapping[card], dtype=torch.long)
            )
        index = []
        for action in actionList:
            index.append(cards_mapping[action])
        actionList_embedding = self.embedding(
            torch.tensor(index, dtype=torch.long)
            )
        outputs = self.attention_layer(actionList_embedding)
        outputs = outputs.sum(dim=0)
        input_vec = torch.cat((card_embedding, outputs))
        outputs = self.fc(input_vec)
        scores = torch.mm(actionList_embedding, outputs.view(1, -1).T)
        scores = scores.reshape(1, -1)[0]
        return F.softmax(scores, dim=0)

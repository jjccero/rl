from typing import Optional, List

import torch
import torch.nn as nn

from pbrl.policy.base import Mlp, Cnn, Rnn, Discrete, Continuous, Deterministic


def _init(module: nn.Module):
    for m in module.modules():
        if isinstance(m, nn.Linear):
            torch.nn.init.zeros_(m.bias)
            torch.nn.init.orthogonal_(m.weight)
        elif isinstance(m, nn.GRU):
            torch.nn.init.zeros_(m.bias_ih_l0)
            torch.nn.init.zeros_(m.bias_hh_l0)
            torch.nn.init.orthogonal_(m.weight_ih_l0)
            torch.nn.init.orthogonal_(m.weight_hh_l0)


class DeterministicActor(nn.Module):
    def __init__(
            self,
            obs_dim: tuple,
            action_dim: int,
            rnn: Optional[str],
            hidden_sizes: List[int],
            activation,
            device
    ):
        super(DeterministicActor, self).__init__()
        self.rnn = rnn
        self.hidden_size = hidden_sizes[-1]
        if len(obs_dim) == 3:
            self.f = Cnn(obs_dim, hidden_sizes, activation)
        else:
            self.f = Mlp(obs_dim, hidden_sizes, activation)
        if self.rnn:
            self.f2 = Rnn(self.hidden_size, activation)
        self.act = Deterministic(self.hidden_size, action_dim)
        _init(self)
        self.device = device
        self.to(self.device)

    def forward(
            self,
            observations,
            states: Optional[torch.Tensor] = None,
            dones: Optional[torch.Tensor] = None
    ):
        x = self.f(observations)
        if self.rnn:
            x, states = self.f2(x, states, dones)
        actions = self.act.forward(x).tanh()
        return actions, states


class Actor(nn.Module):
    def __init__(
            self,
            obs_dim: tuple,
            action_dim: int,
            continuous: bool,
            rnn: Optional[str],
            hidden_sizes: List[int],
            activation,
            device
    ):
        super(Actor, self).__init__()
        self.continuous = continuous
        self.rnn = rnn
        self.hidden_size = hidden_sizes[-1]
        if len(obs_dim) == 3:
            self.f = Cnn(obs_dim, hidden_sizes, activation)
        else:
            self.f = Mlp(obs_dim, hidden_sizes, activation)
        if self.rnn:
            self.f2 = Rnn(self.hidden_size, activation, self.rnn)
        self.dist = Continuous(self.hidden_size, action_dim) if self.continuous \
            else Discrete(self.hidden_size, action_dim)
        _init(self)
        self.device = device
        self.to(self.device)

    def forward(
            self,
            observations,
            states: Optional[torch.Tensor] = None,
            dones: Optional[torch.Tensor] = None
    ):
        x = self.f(observations)
        if self.rnn:
            x, states = self.f2(x, states, dones)
        dist = self.dist.forward(x)
        return dist, states


class DoubleQ(nn.Module):
    def __init__(
            self,
            obs_dim: tuple,
            action_dim: int,
            hidden_sizes: List[int],
            activation,
            device
    ):
        super(DoubleQ, self).__init__()
        self.hidden_size = hidden_sizes[-1]
        if len(obs_dim) == 1:
            self.f1 = Mlp((obs_dim[0] + action_dim,), hidden_sizes, activation)
            self.f2 = Mlp((obs_dim[0] + action_dim,), hidden_sizes, activation)
        else:
            raise NotImplementedError

        self.q1 = Deterministic(self.hidden_size, 1)
        self.q2 = Deterministic(self.hidden_size, 1)
        _init(self)
        self.device = device
        self.to(self.device)

    def forward(self, observations, actions):
        x = torch.cat((observations, actions), dim=-1)
        x1 = self.f1.forward(x)
        q1 = self.q1.forward(x1).squeeze(-1)
        x2 = self.f2.forward(x)
        q2 = self.q2.forward(x2).squeeze(-1)
        return q1, q2


class Critic(nn.Module):
    def __init__(
            self,
            obs_dim: tuple,
            rnn: Optional[str],
            hidden_sizes: List[int],
            activation,
            device
    ):
        super(Critic, self).__init__()
        self.rnn = rnn
        self.hidden_size = hidden_sizes[-1]
        if len(obs_dim) == 3:
            self.f = Cnn(obs_dim, hidden_sizes, activation)
        else:
            self.f = Mlp(obs_dim, hidden_sizes, activation)
        if self.rnn:
            self.f2 = Rnn(self.hidden_size, activation)
        self.value = Deterministic(self.hidden_size, 1)
        _init(self)
        self.device = device
        self.to(self.device)

    def forward(self, observations, states, dones):
        x = self.f.forward(observations)
        if self.rnn:
            x, states = self.f2.forward(x, states, dones)
        values = self.value.forward(x).squeeze(-1)
        return values, states
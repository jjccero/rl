from typing import Optional

import numpy as np
import torch
from gym.spaces import Box, Discrete

from pbrl.policy.net import Actor, Critic
from pbrl.policy.policy import Policy


class PGPolicy(Policy):
    def __init__(
            self,
            critic: bool = True,
            **kwargs
    ):
        super(PGPolicy, self).__init__(**kwargs)
        if isinstance(self.action_space, Box):
            continuous = True
            action_dim = self.action_space.shape[0]
        elif isinstance(self.action_space, Discrete):
            continuous = False
            action_dim = self.action_space.n
        else:
            raise not NotImplementedError('Neither Box or Discrete!')
        self.actor = Actor(
            obs_dim=self.observation_space.shape,
            action_dim=action_dim,
            continuous=continuous,
            rnn=self.rnn,
            hidden_sizes=self.hidden_sizes,
            activation=self.activation,
            device=self.device
        )
        self.critic = Critic(
            obs_dim=self.observation_space.shape,
            rnn=self.rnn,
            hidden_sizes=self.hidden_sizes,
            activation=self.activation,
            device=self.device
        ) if critic else None

    @torch.no_grad()
    def step(
            self,
            observations: np.ndarray,
            states_actor
    ):
        observations = self.n2t(observations)
        dists, states_actor = self.actor.forward(observations, states_actor)
        actions = dists.sample()
        log_probs = dists.log_prob(actions)
        if self.actor.continuous:
            log_probs = log_probs.sum(-1)
        actions = self.t2n(actions)
        log_probs = self.t2n(log_probs)
        return actions, log_probs, states_actor

    @torch.no_grad()
    def act(
            self,
            observations: np.ndarray,
            states_actor
    ):
        observations = self.n2t(observations)
        dists, states_actor = self.actor.forward(observations, states_actor)
        actions = dists.sample()
        actions = self.t2n(actions)
        return actions, states_actor

    def get_values(
            self,
            observations: torch.Tensor,
            states_critic=None,
            dones: Optional[torch.Tensor] = None
    ):
        return self.critic.forward(observations, states_critic, dones)

    def evaluate_actions(
            self,
            observations: torch.Tensor,
            actions: torch.Tensor,
            dones: Optional[torch.Tensor]
    ):
        dist, _ = self.actor.forward(observations, dones=dones)
        log_probs = dist.log_prob(actions)
        dist_entropy = dist.entropy()
        if self.actor.continuous:
            log_probs = log_probs.sum(-1)
        return log_probs, dist_entropy

    def eval(self):
        self.actor.eval()
        if self.critic:
            self.critic.eval()

    def train(self):
        self.actor.train()
        if self.critic:
            self.critic.train()

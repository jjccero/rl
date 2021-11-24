import numpy as np
from gym.spaces import Box


class ReplayBuffer:
    def __init__(
            self,
            buffer_size: int,
            observation_space: Box,
            action_space: Box,

    ):
        self.buffer_size = buffer_size
        self.ptr = 0
        self.len = 0

        self.observations = np.zeros((buffer_size, *observation_space.shape), dtype=float)
        self.actions = np.zeros((buffer_size, *action_space.shape), dtype=float)
        self.observations_next = np.zeros((buffer_size, *observation_space.shape), dtype=float)
        self.rewards = np.zeros(buffer_size)
        self.dones = np.zeros(buffer_size, dtype=float)

    def append(
            self,
            observations: np.ndarray,
            actions: np.ndarray,
            observations_next: np.ndarray,
            rewards: np.ndarray,
            dones: np.ndarray
    ):
        env_num = observations.shape[0]
        for i in range(env_num):
            index = (self.ptr + i) % self.buffer_size
            self.observations[index] = observations[i]
            self.actions[index] = actions[i]
            self.observations_next[index] = observations_next[i]
            self.rewards[index] = rewards[i]
            self.dones[index] = dones[i]

        self.ptr = (self.ptr + env_num) % self.buffer_size
        self.len = min(self.len + env_num, self.buffer_size)

    def sample(self, batch_size: int):
        index = np.random.randint(self.len, size=batch_size)
        return (
            self.observations[index],
            self.actions[index],
            self.observations_next[index],
            self.rewards[index],
            self.dones[index]
        )
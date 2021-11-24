import argparse

import gym
import numpy as np
import torch

from pbrl.algorithms.td3 import TD3, Runner, TD3Policy, ReplayBuffer
from pbrl.common import Logger
from pbrl.env import SubProcVecEnv, DummyVecEnv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str, default='HalfCheetah-v3')
    parser.add_argument('--env_num', type=int, default=1)
    parser.add_argument('--env_num_test', type=int, default=10)
    parser.add_argument('--episode_num_test', type=int, default=10)
    parser.add_argument('--timestep', type=int, default=1000000)
    parser.add_argument('--log_dir', type=str, default=None)
    parser.add_argument('--test_interval', type=int, default=5000)
    parser.add_argument('--log_interval', type=int, default=5000)
    parser.add_argument('--subproc', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--seed', type=int, default=0)

    parser.add_argument('--start_timestep', type=int, default=25000)
    parser.add_argument('--buffer_size', type=int, default=1000000)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--step_per_update', type=int, default=1)
    parser.add_argument('--policy_freq', type=int, default=2)
    parser.add_argument('--chunk_len', type=int, default=None)
    parser.add_argument('--rnn', type=str, default=None)

    parser.add_argument('--gamma', type=float, default=0.99)
    parser.add_argument('--tau', type=float, default=0.005)
    parser.add_argument('--noise_clip', type=float, default=0.5)
    parser.add_argument('--noise_explore', type=float, default=0.1)
    parser.add_argument('--noise_policy', type=float, default=0.2)

    parser.add_argument('--obs_norm', action='store_true')
    parser.add_argument('--reward_norm', action='store_true')

    parser.add_argument('--lr_actor', type=float, default=3e-4)
    parser.add_argument('--lr_critic', type=float, default=3e-4)

    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    log_dir = args.log_dir if args.log_dir is not None else '{}-{}'.format(args.env, args.seed)
    filename_log = 'result/{}'.format(log_dir)

    logger = Logger(filename_log)
    # define train and test environment
    env_train = DummyVecEnv([lambda: gym.make(args.env) for _ in range(args.env_num)])
    env_test = SubProcVecEnv([lambda: gym.make(args.env) for _ in range(args.env_num_test)])
    env_train.seed(args.seed)
    env_test.seed(args.seed)
    # define policy
    policy = TD3Policy(
        noise_explore=args.noise_policy,
        noise_clip=args.noise_clip,
        observation_space=env_train.observation_space,
        action_space=env_train.action_space,
        rnn=args.rnn,
        hidden_sizes=[64, 64],
        activation=torch.nn.Tanh,
        obs_norm=args.obs_norm,
        reward_norm=args.reward_norm,
        gamma=args.gamma,
        device=torch.device('cuda:0') if torch.cuda.is_available() else torch.device('cpu')
    )
    buffer = ReplayBuffer(
        buffer_size=args.buffer_size,
        observation_space=env_train.observation_space,
        action_space=env_train.action_space
    )
    # define trainer for the task
    trainer = TD3(
        policy=policy,
        buffer=buffer,
        batch_size=args.batch_size,
        gamma=args.gamma,
        noise_target=args.noise_policy,
        noise_clip=args.noise_clip,
        policy_freq=args.policy_freq,
        tau=args.tau,
        lr_actor=args.lr_actor,
        lr_critic=args.lr_critic
    )

    # define train and test runner
    runner_train = Runner(env_train, policy)
    runner_test = Runner(env_test, policy)

    # runner_train.reset()
    # runner_train.run(buffer_size=args.start_timestep, buffer=buffer)

    trainer.learn(
        timestep=args.timestep,
        runner_train=runner_train,
        buffer_size=args.step_per_update,
        logger=logger,
        log_interval=args.log_interval,
        runner_test=runner_test,
        test_interval=args.test_interval,
        episode_test=args.episode_num_test
    )


if __name__ == '__main__':
    main()

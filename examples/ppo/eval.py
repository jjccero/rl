import argparse

import gym
import torch

from pbrl.algorithms.ppo import PGPolicy
from pbrl.algorithms.ppo import PPO, Runner
from pbrl.env import DummyVecEnv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str, default='CartPole-v0')
    parser.add_argument('--log_dir', type=str, default=None)
    parser.add_argument('--subproc', action='store_true')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--rnn', type=str, default=None)
    parser.add_argument('--obs_norm', action='store_true')

    parser.add_argument('--env_num_test', type=int, default=1)
    parser.add_argument('--episode_num_test', type=int, default=1)
    parser.add_argument('--render', type=float, default=0.005)

    args = parser.parse_args()
    torch.manual_seed(args.seed)

    log_dir = args.log_dir if args.log_dir is not None else '{}-{}'.format(args.env, args.seed)
    filename_policy = 'result/{}/policy.pkl'.format(log_dir)
    # define test environment
    env_test = DummyVecEnv([lambda: gym.make(args.env) for _ in range(args.env_num_test)])
    env_test.seed(args.seed)
    # define policy
    policy = PGPolicy(
        observation_space=env_test.observation_space,
        action_space=env_test.action_space,
        rnn=args.rnn,
        hidden_sizes=[64, 64],
        activation=torch.nn.Tanh,
        obs_norm=args.obs_norm,
        critic=False,
        device=torch.device('cuda:0') if torch.cuda.is_available() else torch.device('cpu')
    )
    # load policy from disk
    PPO.load(filename_policy, policy)
    # define test runner
    runner_test = Runner(env_test, policy, render=args.render)
    while True:
        try:
            runner_test.reset()
            policy.eval()
            test_info = runner_test.run(episode_num=args.episode_num_test)
            print(test_info)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
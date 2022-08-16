import random
import string

import pytest
from docopt import DocoptExit
from tabulate import tabulate

import ML_for_Battery_Design.src.main as main

valid_modes = [
    "train_online",
    "train_offline",
    "generate_data",
    "analyze_sim",
    "evaluate",
]
valid_sim = ["linear_ode_system"]
valid_summary = ["FC", "LSTM", "CNN"]

random_input = [
    "",
    "".join(random.choices(string.ascii_letters, k=random.randrange(10))),
]


@pytest.mark.parametrize("filename", random_input + [None])
def test_main_train_online(filename, capsys):
    sim = random.choice(random_input)
    summary = random.choice(random_input)
    if filename is not None:
        args = main.main(["train_online", sim, summary, filename])
    else:
        args = main.main(["train_online", sim, summary])
    out, err = capsys.readouterr()
    assert (
        out
        == "Interface user input:\n"
        + tabulate(list(args.items()), missingval="None")
        + "\n"
    )
    assert err == ""
    assert bool(args["train_online"])
    assert not bool(args["train_offline"])
    assert not bool(args["generate_data"])
    assert not bool(args["analyze_sim"])
    assert not bool(args["evaluate"])
    assert args["<sim_model>"] == sim
    assert args["<summary_net>"] == summary
    assert args["<filename>"] == filename
    assert args["<data_name>"] is None


@pytest.mark.parametrize("filename", random_input + [None])
def test_main_train_offline(filename, capsys):
    sim = random.choice(random_input)
    data = random.choice(random_input)
    summary = random.choice(random_input)
    if filename is not None:
        args = main.main(["train_offline", sim, data, summary, filename])
    else:
        args = main.main(["train_offline", sim, data, summary])
    out, err = capsys.readouterr()
    assert (
        out
        == "Interface user input:\n"
        + tabulate(list(args.items()), missingval="None")
        + "\n"
    )
    assert err == ""
    assert bool(args["train_offline"])
    assert not bool(args["train_online"])
    assert not bool(args["generate_data"])
    assert not bool(args["analyze_sim"])
    assert not bool(args["evaluate"])
    assert args["<sim_model>"] == sim
    assert args["<data_name>"] == data
    assert args["<summary_net>"] == summary
    assert args["<filename>"] == filename


def test_main_generate_data(capsys):
    sim = random.choice(random_input)
    data = random.choice(random_input)
    args = main.main(["generate_data", sim, data])
    out, err = capsys.readouterr()
    assert (
        out
        == "Interface user input:\n"
        + tabulate(list(args.items()), missingval="None")
        + "\n"
    )
    assert err == ""
    assert bool(args["generate_data"])
    assert not bool(args["train_online"])
    assert not bool(args["train_offline"])
    assert not bool(args["analyze_sim"])
    assert not bool(args["evaluate"])
    assert args["<sim_model>"] == sim
    assert args["<data_name>"] == data
    assert args["<summary_net>"] is None
    assert args["<filename>"] is None


@pytest.mark.parametrize("filename", random_input + [None])
def test_main_analyze_sim(filename, capsys):
    sim = random.choice(random_input)
    if filename is not None:
        args = main.main(["analyze_sim", sim, filename])
    else:
        args = main.main(["analyze_sim", sim])
    out, err = capsys.readouterr()
    assert (
        out
        == "Interface user input:\n"
        + tabulate(list(args.items()), missingval="None")
        + "\n"
    )
    assert err == ""
    assert bool(args["analyze_sim"])
    assert not bool(args["train_online"])
    assert not bool(args["train_offline"])
    assert not bool(args["generate_data"])
    assert not bool(args["evaluate"])
    assert args["<sim_model>"] == sim
    assert args["<filename>"] == filename
    assert args["<data_name>"] is None
    assert args["<summary_net>"] is None


@pytest.mark.parametrize("filename", random_input + [None])
def test_main_evaluate(filename, capsys):
    sim = random.choice(random_input)
    data = random.choice(random_input)
    if filename is not None:
        args = main.main(["evaluate", sim, data, filename])
    else:
        args = main.main(["evaluate", sim, data])
    out, err = capsys.readouterr()
    assert (
        out
        == "Interface user input:\n"
        + tabulate(list(args.items()), missingval="None")
        + "\n"
    )
    assert err == ""
    assert bool(args["evaluate"])
    assert not bool(args["train_online"])
    assert not bool(args["train_offline"])
    assert not bool(args["generate_data"])
    assert not bool(args["analyze_sim"])
    assert args["<sim_model>"] == sim
    assert args["<data_name>"] == data
    assert args["<filename>"] == filename
    assert args["<summary_net>"] is None


@pytest.mark.parametrize("random_input", random_input)
def test_main_random_input(random_input):
    with pytest.raises(DocoptExit):
        main.main([random_input] * random.randrange(10))

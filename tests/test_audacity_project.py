from manokee.audacity.project import parse as parse_aup


def test_load_audacity_project():
    project = parse_aup("tests/assets/audacity-projects/simple.aup")
    assert project.get_project_dir() == "./tests/assets/audacity-projects"
    assert (
        project.get_blockfile_path("e0000cc1.au")
        == "./tests/assets/audacity-projects/simple_data/e00/d00/e0000cc1.au"
    )
    assert list(project.get_wave_tracks()) == []
    label_track = project.get_label_track()
    assert label_track.get_name() == "ofs=100"
    assert list(label_track.get_label_positions()) == [
        1,
        3,
        5,
        7.5,
        10,
        12.5,
        15,
        17.5,
        20,
    ]

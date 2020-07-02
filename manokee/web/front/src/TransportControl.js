import React, {Component} from "react";
import Collapsible from "react-collapsible";

export class TransportControl extends Component {
  constructor(props) {
    super(props);
    this.state = {
      beat_number: 0,
    };
  }

  render() {
    const {configuration = {}} = this.props.session || {};
    const {
      tape_length = '',
    } = configuration || {};

    return <div>
      <div>Tape length: {tape_length}</div>
      <div>Transport state: <span>unknown</span>.</div>
      <div>
        Current position: {this.props.current_position}
        ({this.props.current_beat}).
      </div>
      <div>
        <input className="image-button menu-image-button" type="image" src="/auto-rewind.svg"/>
      </div>
      <Collapsible trigger={<button>Go to beat...</button>}>
        <input
          id="beat-number" type="number" value={this.state.beat_number + 1}
          onChange={evt => this.updateBeatNumber(evt)}/>
        <button
          onClick={evt => this.props.onGoToBeat(this.state.beat_number)}>
          Go
        </button>
      </Collapsible>
      <div>
        Go to bar:
        <button>0</button>
        <button>{this.props.current_bar + 0}</button>
        <button className="highlighted-button">{this.props.current_bar + 1}</button>
        <button>{this.props.current_bar + 2}</button>
      </div>
    </div>;
  }

  updateBeatNumber(evt) {
    this.setState({
      beat_number: parseInt(evt.target.value) - 1,
    });
  }
}
import React from 'react';
import ReactDOM from 'react-dom';

import {App, onLoad} from './app';

window.onload = onLoad;

ReactDOM.render(
  <App current_position="?" current_beat="--" />,
  document.getElementById('app')
);

module.hot.accept();

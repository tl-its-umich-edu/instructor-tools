import React from 'react';
import { Globals } from './interfaces';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import ToolsHome from './components/ToolsHome';
import AltTextHome from './components/AltTextHome';


interface AppProps {
  globals: Globals
}

function App (props: AppProps) {

  return (
    <div id='root'>
      <Router>
        <Routes>
          <Route path='/' element={
            <ToolsHome {...props} />
          }/>
          <Route path='alt-text-helper' element={
            <AltTextHome {...props}/>
          }/>          
        </Routes>
      </Router>
    </div>
  );
}
export default App;
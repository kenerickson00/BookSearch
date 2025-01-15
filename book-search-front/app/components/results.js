'use client';
import { Backdrop, Container, IconButton, Tooltip, Typography } from "@mui/material";
import CloseIcon from '@mui/icons-material/Close';

export default function ResultsPage(props) {
    {/* props
        isOpen: boolean
        respData: string[] | null
        errorData: string[] | null
        close: function
        */}
    
    const isError = props.errorData !== null;
    const isEmpty = isError ? true : (props.respData === null || !Array.isArray(props.respData) || props.respData.length < 1);
    const title = isError ? 'Error: Search Failed' : 'Search Results';
    const otherMessage = !isError && props.respData !== null && !Array.isArray(props.respData)
    const results = isError || isEmpty ? 
        (otherMessage ? [props.respData] : ["No matching books found. Try adjusting your question and searching again!"]) 
        : props.respData;

    console.log(isError, isEmpty, results);
    const PBody = (props) => {
        return <div className={isError ? "ebody" : "pbody"}>
            <Typography variant="body1">{props.text}</Typography>
        </div>
    };

    return (
        props.isOpen && (props.respData !== null || props.errorData !== null) ?
        <Backdrop
            sx={(theme) => ({ color: '#fff', zIndex: theme.zIndex.drawer + 1 })}
            open={props.isOpen}>
            <div className={isError? "eaper" : "paper"} style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
                alignItems: 'flex-start',
                overflowY: 'auto',
                padding: '1em'
            }}>
                <div style={{
                    display: 'flex',
                    flexDirection: 'row',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    width: '100%'
                }}>
                    <Typography variant='h3'>{title}</Typography>
                    <Tooltip title="Return Home" placement="right">
                        <IconButton variant="filled" color="inherit" onClick={props.close}>
                            <CloseIcon fontSize="large" />
                        </IconButton>
                    </Tooltip>
                </div>

                {isError ? <PBody text={props.errorData} /> : otherMessage ?  
                <>
                    <Typography variant='h5' style={{ marginBottom: '2.5vh' }}>
                        No books found
                    </Typography>
                    <PBody text={results[0]} />
                </> :
                <>
                    <Typography variant='h5'>
                        {`${results.length} books found`}
                    </Typography>
                    <div className="results">
                        {results !== null ? results.map((book, index) => {
                            return (
                                <div key={`book-${index}`} className={isError ? "ebody" : "pbody"} style={{
                                    display: 'flex',
                                    flexDirection: 'row',
                                    justifyContent: 'flex-start',
                                    alignItems: 'center',
                                    flexWrap: 'wrap'
                                }}>
                                    <Typography variant='body1' style={{ fontWeight: "bold", marginRight: '0.3em' }}>
                                        {`"${book.title}" by ${book.author}`}
                                    </Typography>
                                    {"description" in book ? 
                                    <Typography variant='body1'>
                                        {" - "+ book.description}
                                    </Typography> : ""}
                                </div>
                            )
                        }) : ""}
                    </div>
                </>}
            </div>
        </Backdrop> : ""
    );
}
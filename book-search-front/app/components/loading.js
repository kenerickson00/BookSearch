'use client';
import { Backdrop, Skeleton } from "@mui/material";

export default function LoadingPage(props) {
    {/* props
        isOpen: boolean
        */}
    return (
        <Backdrop
            sx={(theme) => ({ color: '#fff', zIndex: theme.zIndex.drawer + 1 })}
            open={props.isOpen}>
            <div className="paper" style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
                alignItems: 'flex-start',
                padding: '1em'
            }}>
                <Skeleton variant="circular" width={"5vh"} height={"5vh"} style={{ marginTop: "2vh" }} />
                <Skeleton variant="rounded" width={"70vw"} height={"7.5vh"} style={{ marginBottom: "5vh", marginTop: "1vh"}} />
                <Skeleton variant="rounded" width={"70vw"} height={"25vh"} style={{ marginBottom: "2vh" }} />
                <Skeleton variant="rounded" width={"70vw"} height={"25vh"} />
            </div>
        </Backdrop>
    );
}